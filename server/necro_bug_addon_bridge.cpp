// SPDX-License-Identifier: GPL-3.0-or-later
// NecroCore server-side receiver for dedicated NECROBUG addon messages.
// Called only by the explicit prefix check in ChatHandler.cpp.
#include "Player.h"
#include "ChatPackets.h"
#include "WorldSession.h"
#include "Language.h"
#include "Common.h"
#include <algorithm>
#include <chrono>
#include <cstdint>
#include <cstdlib>
#include <filesystem>
#include <system_error>
#include <fstream>
#include <mutex>
#include <string>
#include <unordered_map>
#include <vector>

namespace {
// Optional NECROBUG_INBOX environment variable supplies an absolute report-log path.
// Otherwise use the current worldserver working directory (see documentation).
std::filesystem::path InboxPath()
{
    if (char const* configured = std::getenv("NECROBUG_INBOX"))
        if (*configured)
            return std::filesystem::path(configured);
    return std::filesystem::current_path() / "NecroBugTracker" / "inbox" / "received.log";
}
struct Pending {
    std::vector<std::string> chunks;
    std::vector<bool> seen;
    size_t received = 0;
    std::chrono::steady_clock::time_point since = std::chrono::steady_clock::now();
};
std::mutex gMutex;
std::unordered_map<std::string, Pending> gPending;
uint64_t gSequence = 0;

// Server-to-client receipt. Same BfA chat-packet path used by AddonChannelCommandHandler.
// A receipt is emitted only once the entire report is appended and closed successfully.
void SendReceipt(Player* player, std::string const& requestId, bool saved, std::string const& detail)
{
    if (!player || !player->GetSession())
        return;

    WorldPackets::Chat::Chat reply;
    std::string message = "NBA3|" + requestId + (saved ? "|OK|" : "|ERR|") + detail;
    reply.Initialize(CHAT_MSG_WHISPER, LANG_ADDON, player, player, message, 0, "", DEFAULT_LOCALE, "NECROBUG");
    player->GetSession()->SendPacket(reply.Write());
}
bool IsDigits(std::string const& s) {
    return !s.empty() && s.size() <= 3 && std::all_of(s.begin(), s.end(), [](unsigned char c) { return c >= '0' && c <= '9'; });
}
}

// Returns true when packet has been accepted as a valid report fragment.
bool NecroBugHandleAddon(Player* player, std::string const& text)
{
    if (!player || text.size() > 240 || text.rfind("NBR2|", 0) != 0)
        return false;
    size_t a = text.find('|', 5);
    if (a == std::string::npos) return false;
    size_t b = text.find('|', a + 1);
    if (b == std::string::npos) return false;
    size_t c = text.find('|', b + 1);
    if (c == std::string::npos) return false;
    std::string rid = text.substr(5, a - 5);
    std::string indexStr = text.substr(a + 1, b - a - 1);
    std::string totalStr = text.substr(b + 1, c - b - 1);
    if (rid.empty() || rid.size() > 32 || !IsDigits(indexStr) || !IsDigits(totalStr)) return false;
    if (!std::all_of(rid.begin(), rid.end(), [](unsigned char ch) {
        return (ch >= '0' && ch <= '9') || ch == '-'; })) return false;
    int index = std::stoi(indexStr);
    int total = std::stoi(totalStr);
    if (index < 1 || total < 1 || total > 100 || index > total) return false;
    std::string content = text.substr(c + 1);
    if (content.size() > 160 || content.find('\r') != std::string::npos || content.find('\n') != std::string::npos) return false;
    std::string key = std::to_string(reinterpret_cast<std::uintptr_t>(player)) + ':' + rid;
    std::lock_guard<std::mutex> lock(gMutex);
    auto now = std::chrono::steady_clock::now();
    for (auto it = gPending.begin(); it != gPending.end();) {
        if (now - it->second.since > std::chrono::minutes(2)) it = gPending.erase(it);
        else ++it;
    }
    if (gPending.find(key) == gPending.end() && gPending.size() >= 128) return false;
    Pending& p = gPending[key];
    if (p.chunks.empty()) { p.chunks.resize(total); p.seen.resize(total, false); }
    if (p.chunks.size() != static_cast<size_t>(total)) { gPending.erase(key); return false; }
    if (!p.seen[index - 1]) { p.chunks[index - 1] = std::move(content); p.seen[index - 1] = true; ++p.received; }
    if (p.received == p.chunks.size()) {
        std::string record;
        for (std::string const& part : p.chunks) record += part;
        // Avoid trusting the user-supplied character name or report ID to identify server records.
        std::string uniqueRid = rid + '-' + std::to_string(++gSequence);
        bool saved = false;
        {
            std::filesystem::path inbox = InboxPath();
            std::error_code ec;
            std::filesystem::create_directories(inbox.parent_path(), ec);
            std::ofstream output;
            if (!ec)
                output.open(inbox, std::ios::app | std::ios::binary);
            if (output)
            {
                output << "NB2|" << uniqueRid << '|' << player->GetName() << '|' << record << '\n';
                output.flush();
                saved = output.good();
                output.close();
                saved = saved && !output.fail();
            }
        }
        gPending.erase(key);
        // Receipt ID corresponds to the durable inbox record. The dashboard assigns
        // its own numeric ticket number later, when SQLite ingestion occurs.
        SendReceipt(player, rid, saved, saved ? uniqueRid : "WRITE_FAILED");
        return saved;
    }
    return true;
}
