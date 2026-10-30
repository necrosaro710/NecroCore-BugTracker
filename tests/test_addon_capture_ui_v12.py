"""Static guard against future regressions exposing the /bug UI in screenshots.

This does not replace an actual screenshot test in the WoW 8.3.7 client.
"""
from pathlib import Path
import unittest

ADDON=Path(__file__).resolve().parents[1]/'client/NecroBugTracker/NecroBugTracker.lua'

class BugWindowHiddenDuringCapture(unittest.TestCase):
    def test_ui_is_hidden_and_redrawn_before_screen_capture(self):
        text=ADDON.read_text(encoding='utf-8')
        start=text.index("shotButton:SetScript('OnClick'")
        end=text.index('local cancel=CreateFrame', start)
        handler=text[start:end]
        self.assertIn("f:Hide()",handler)
        self.assertLess(handler.index("f:Hide()"),handler.index("Screenshot()"))
        self.assertIn('frames<2 or elapsed<0.4',handler)
        self.assertIn('if f:IsShown() then f:Hide() end',handler)
        self.assertIn("shotDelay:SetScript('OnUpdate'",handler)
        self.assertIn('shotIssued=true',handler)
        self.assertIn('C_Timer.After(3.0,finishScreenshot)',handler)
        # No pre-shot chat log that would itself enter the screenshot.
        self.assertFalse(any(line.strip().startswith('print(')
                             for line in handler[handler.index('shotInProgress=true'):].splitlines()))

    def test_dialog_restores_after_screenshot_event(self):
        text=ADDON.read_text(encoding='utf-8')
        self.assertIn("shotWatcher:RegisterEvent('SCREENSHOT_SUCCEEDED')",text)
        self.assertIn("shotWatcher:RegisterEvent('SCREENSHOT_FAILED')",text)
        self.assertIn("C_Timer.After(0.15,finishScreenshot)",text)
        self.assertIn('if shotInProgress then return end',text)
        self.assertIn("-- Never risk capturing the report window by taking an immediate screenshot.",text)

if __name__=='__main__': unittest.main()
