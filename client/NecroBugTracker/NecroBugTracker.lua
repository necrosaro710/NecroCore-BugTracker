-- SPDX-License-Identifier: GPL-3.0-or-later
NecroBugLocalBackup = NecroBugLocalBackup or {}
local function enc(v)
  return (tostring(v or ''):gsub('([^%w%-%._~ ])',function(c) return string.format('%%%02X',string.byte(c)) end):gsub(' ','%%20'))
end
local function targetInfo()
  local guid=UnitGUID('target') or ''
  local parts={strsplit('-',guid)}
  return UnitName('target') or '(no target)',guid,parts[1] or '',parts[6] or ''
end
local function quests()
  local t={}
  if C_QuestLog and C_QuestLog.GetNumQuestLogEntries and C_QuestLog.GetInfo then
    for i=1,math.min(C_QuestLog.GetNumQuestLogEntries(),500) do
      local q=C_QuestLog.GetInfo(i)
      if q and not q.isHeader then t[#t+1]=tostring(q.questID or 0)..': '..(q.title or '') end
    end
  end
  return table.concat(t,' ; ')
end
if C_ChatInfo and C_ChatInfo.RegisterAddonMessagePrefix then C_ChatInfo.RegisterAddonMessagePrefix('NECROBUG') end
local f=CreateFrame('Frame','NecroBugDialog',UIParent,'BasicFrameTemplateWithInset')
f:SetSize(560,570);f:SetPoint('CENTER');f:SetMovable(true);f:EnableMouse(true)
f:RegisterForDrag('LeftButton');f:SetScript('OnDragStart',f.StartMoving);f:SetScript('OnDragStop',f.StopMovingOrSizing)
f:Hide();f.TitleText:SetText('NecroCore | New Bug Report')
local label=f:CreateFontString(nil,'OVERLAY','GameFontNormal');label:SetPoint('TOPLEFT',18,-82);label:SetWidth(520);label:SetJustifyH('LEFT')
local qlabel=f:CreateFontString(nil,'OVERLAY','GameFontHighlightSmall');qlabel:SetPoint('TOPLEFT',18,-117);qlabel:SetText('Related quest / quest ID (optional):')
local quest=CreateFrame('EditBox',nil,f,'InputBoxTemplate');quest:SetSize(502,25);quest:SetPoint('TOPLEFT',28,-135);quest:SetAutoFocus(false)
-- Priority is chosen in-game and transmitted as the 15th field. Medium is the default.
local selectedPriority='Medium'
local plabel=f:CreateFontString(nil,'OVERLAY','GameFontHighlightSmall')
plabel:SetPoint('TOPLEFT',18,-172)
plabel:SetText('Priority (select before submitting):')
local priorityButtons={}
local priorityNames={'Low','Medium','High'}
local function setPriority(value)
  selectedPriority=value
  for _,name in ipairs(priorityNames) do
    priorityButtons[name]:SetChecked(name==value)
  end
end
for i,name in ipairs(priorityNames) do
  local button=CreateFrame('CheckButton',nil,f,'UICheckButtonTemplate')
  button:SetSize(25,25)
  button:SetPoint('TOPLEFT',24+(i-1)*147,-195)
  button:SetScript('OnClick',function() setPriority(name) end)
  local caption=f:CreateFontString(nil,'OVERLAY','GameFontHighlight')
  caption:SetPoint('LEFT',button,'RIGHT',3,0)
  caption:SetText(name)
  priorityButtons[name]=button
end
setPriority('Medium')
local nlabel=f:CreateFontString(nil,'OVERLAY','GameFontHighlightSmall');nlabel:SetPoint('TOPLEFT',18,-236);nlabel:SetText('What happened and how do you reproduce it?')
-- Notes editor: the scroll child MUST have a nonzero height before it is shown.
-- Otherwise the text field occupies no space and cannot be clicked or typed into.
local scroll=CreateFrame('ScrollFrame',nil,f,'UIPanelScrollFrameTemplate')
scroll:SetPoint('TOPLEFT',20,-256);scroll:SetPoint('BOTTOMRIGHT',-40,61)
local editorBackground=scroll:CreateTexture(nil,'BACKGROUND')
editorBackground:SetAllPoints(scroll)
editorBackground:SetColorTexture(0.13,0.15,0.19,0.82)
local notes=CreateFrame('EditBox',nil,scroll)
notes:SetSize(455,215) -- Nonzero initial height fixes the invisible/unfocusable notes box.
notes:SetMultiLine(true)
notes:SetFontObject('ChatFontNormal')
notes:SetAutoFocus(false)
scroll:SetScrollChild(notes)
local hint=scroll:CreateFontString(nil,'OVERLAY','GameFontDisableSmall')
hint:SetPoint('TOPLEFT',scroll,'TOPLEFT',8,-9)
hint:SetWidth(425)
hint:SetJustifyH('LEFT')
hint:SetText('Click here to type your bug description and reproduction steps...')
local function updateHint()
  if notes:HasFocus() or notes:GetText()~='' then hint:Hide() else hint:Show() end
end
notes:SetScript('OnEscapePressed',function(self) self:ClearFocus() end)
notes:SetScript('OnEditFocusGained',updateHint)
notes:SetScript('OnEditFocusLost',updateHint)
notes:SetScript('OnTextChanged',function(self)
  self:SetHeight(math.max(215,(self:GetStringHeight() or 0)+25))
  updateHint()
end)
-- Allow clicking anywhere in the empty editor area to start writing.
scroll:SetScript('OnMouseDown',function(_,button)
  if button=='LeftButton' then notes:SetFocus() end
end)
quest:SetScript('OnTabPressed',function(self)
  self:ClearFocus()
  notes:SetFocus()
end)
local save=CreateFrame('Button',nil,f,'UIPanelButtonTemplate');save:SetSize(142,28);save:SetPoint('BOTTOMRIGHT',-17,15);save:SetText('Submit to server')
local shotEpoch=nil
local shotInProgress=false
local shotIssued=false
local shotWatcher=CreateFrame('Frame')
local shotDelay=CreateFrame('Frame') -- reused for every screenshot; no leaking UI frames
shotWatcher:RegisterEvent('SCREENSHOT_SUCCEEDED')
shotWatcher:RegisterEvent('SCREENSHOT_FAILED')
local shotButton=CreateFrame('Button',nil,f,'UIPanelButtonTemplate')
shotButton:SetSize(157,28);shotButton:SetPoint('BOTTOMLEFT',17,15)
shotButton:SetText('Take Screenshot')
local function finishScreenshot()
  if not shotInProgress then return end
  shotInProgress=false
  shotIssued=false
  shotButton:Enable()
  shotButton:SetText(shotEpoch and 'Screenshot taken' or 'Take Screenshot')
  f:Show()
end
shotWatcher:SetScript('OnEvent',function(_,event)
  if not shotInProgress or not shotIssued then return end
  if event=='SCREENSHOT_FAILED' then
    shotEpoch=nil
    print('|cffff4444NecroBug:|r Screenshot failed. Please try again.')
  elseif event=='SCREENSHOT_SUCCEEDED' then
    print('|cff00ff00NecroBug:|r Screenshot saved. The PC helper will attach it after you submit.')
  end
  -- Keep the report frame hidden until WoW reports the screenshot was taken.
  C_Timer.After(0.15,finishScreenshot)
end)
shotButton:SetScript('OnClick',function()
  if shotInProgress then return end
  -- Never risk capturing the report window by taking an immediate screenshot.
  if not C_Timer or not C_Timer.After or type(Screenshot)~='function' then
    print('|cffff4444NecroBug:|r Screenshot support is unavailable in this client.')
    return
  end
  shotInProgress=true
  shotIssued=false
  shotEpoch=nil
  shotButton:Disable()
  f:Hide()
  -- Let the UI redraw after the dialog disappears before taking a screenshot.
  -- Wait multiple frames even at a lower frame rate: the hidden dialog must not be pictured.
  local frames=0
  local elapsed=0
  shotDelay:SetScript('OnUpdate',function(self,dt)
    frames=frames+1
    elapsed=elapsed+dt
    if frames<2 or elapsed<0.4 then return end
    self:SetScript('OnUpdate',nil)
    if not shotInProgress then return end
    if f:IsShown() then f:Hide() end
    shotEpoch=GetServerTime()
    shotIssued=true
    Screenshot()
    -- Recovery for clients that do not emit screenshot completion events.
    -- The report remains hidden through the actual Screenshot() call.
    C_Timer.After(3.0,finishScreenshot)
  end)
  -- Do not print a chat message before Screenshot(): it would appear in the image.
end)
local cancel=CreateFrame('Button',nil,f,'UIPanelButtonTemplate');cancel:SetSize(90,28);cancel:SetPoint('RIGHT',save,'LEFT',-8,0);cancel:SetText('Cancel');cancel:SetScript('OnClick',function() f:Hide() end)
local snap={};local queue={};local timer=0;local pending={}
local mode='Bug'
local bugTab=CreateFrame('Button',nil,f,'UIPanelButtonTemplate')
bugTab:SetSize(105,25);bugTab:SetPoint('TOPLEFT',18,-33);bugTab:SetText('Bugs')
local ideaTab=CreateFrame('Button',nil,f,'UIPanelButtonTemplate')
ideaTab:SetSize(105,25);ideaTab:SetPoint('LEFT',bugTab,'RIGHT',9,0);ideaTab:SetText('Ideas')
-- Invisible click targets are parented to the frame, NOT to disabled buttons.
local bugHit=CreateFrame('Button',nil,f)
bugHit:SetAllPoints(bugTab)
bugHit:SetFrameLevel(bugTab:GetFrameLevel()+2)
local ideaHit=CreateFrame('Button',nil,f)
ideaHit:SetAllPoints(ideaTab)
ideaHit:SetFrameLevel(ideaTab:GetFrameLevel()+2)
local function choose(tab)
  mode=(tab=='Idea' and 'Idea' or 'Bug')
  f.TitleText:SetText('NecroCore | '..(mode=='Idea' and 'Submit an Idea' or 'New Bug Report'))
  qlabel:SetText(mode=='Idea' and 'Idea title / feature name:' or 'Related quest / quest ID (optional):')
  nlabel:SetText(mode=='Idea' and 'Describe your idea or suggested improvement:' or 'What happened and how do you reproduce it?')
  hint:SetText(mode=='Idea' and 'Click here to describe your idea...' or 'Click here to type your bug description and reproduction steps...')
  -- Selected tab = enabled red artwork; inactive tab = disabled gray artwork.
  -- Transparent click-catchers above both tab buttons keep both tabs clickable.
  local bugNormal=bugTab:GetNormalTexture()
  local ideaNormal=ideaTab:GetNormalTexture()
  if bugNormal then bugNormal:SetDesaturated(false);bugNormal:SetAlpha(1) end
  if ideaNormal then ideaNormal:SetDesaturated(false);ideaNormal:SetAlpha(1) end
  if mode=='Idea' then
    ideaTab:Enable()
    bugTab:Disable()
  else
    bugTab:Enable()
    ideaTab:Disable()
  end
  bugHit:Enable()
  ideaHit:Enable()
  local bc=bugTab:GetFontString()
  local ic=ideaTab:GetFontString()
  if bc then bc:SetTextColor(mode=='Bug' and 1 or 0.65,mode=='Bug' and 0.82 or 0.65,mode=='Bug' and 0 or 0.65) end
  if ic then ic:SetTextColor(mode=='Idea' and 1 or 0.65,mode=='Idea' and 0.82 or 0.65,mode=='Idea' and 0 or 0.65) end
  updateHint()
end
bugTab:SetScript('OnClick',function() choose('Bug') end)
ideaTab:SetScript('OnClick',function() choose('Idea') end)
bugHit:SetScript('OnClick',function() choose('Bug') end)
ideaHit:SetScript('OnClick',function() choose('Idea') end)
local function open(which)
  if shotInProgress then return end
  choose(which=='Idea' and 'Idea' or 'Bug')
  local name,guid,typ,entry=targetInfo();local map=C_Map and C_Map.GetBestMapForUnit and C_Map.GetBestMapForUnit('player') or 0
  local p=map and C_Map and C_Map.GetPlayerMapPosition and C_Map.GetPlayerMapPosition(map,'player')
  snap={name=name,guid=guid,typ=typ,entry=entry,map=map or 0,x=p and p.x*100 or 0,y=p and p.y*100 or 0,zone=GetZoneText() or '',subzone=GetSubZoneText() or '',char=UnitName('player') or '',realm=GetRealmName() or '',quest_log=quests()}
  label:SetText(mode=='Idea' and ('Idea from '..snap.char..' in '..snap.zone) or ('Target: '..name..'  ['..typ..' '..entry..']'));quest:SetText('');notes:SetText('');setPriority('Medium');shotEpoch=nil;shotButton:Enable();shotButton:SetText('Take Screenshot');scroll:SetVerticalScroll(0);f:Show();quest:SetFocus();updateHint()
end
local function transport(record)
  local rid=tostring(GetServerTime())..'-'..tostring(math.random(100000,999999))
  local size=130;local total=math.ceil(#record/size)
  if total>100 then print('|cffff4444NecroBug:|r Notes too long.');return false end
  for i=1,total do
    queue[#queue+1]={rid=rid,last=(i==total),text='NBR2|'..rid..'|'..i..'|'..total..'|'..record:sub((i-1)*size+1,i*size)}
  end
  pending[rid]={queuedAt=GetTime()}
  return rid
end
save:SetScript('OnClick',function()
  local idea=(mode=='Idea')
  if idea and quest:GetText():match('^%s*$') then print('|cffff4444NecroBug:|r Enter an idea title.');return end
  if notes:GetText():match('^%s*$') then print('|cffff4444NecroBug:|r Enter a description.');return end
  -- Fields 1-14: original report. Field 15: user's selected priority. Field 16: category.
  local fields={snap.char,snap.realm,idea and quest:GetText() or snap.name,snap.guid,snap.typ,snap.entry,snap.map,string.format('%.3f',snap.x),string.format('%.3f',snap.y),snap.zone,snap.subzone,idea and '' or quest:GetText(),notes:GetText(),snap.quest_log,selectedPriority,idea and 'Idea' or 'Bug'}
  -- Only append the 17th field when a screenshot was taken. Old reports stay compatible.
  -- The worldserver continues forwarding text; image bytes are NEVER sent via addon chat.
  if shotEpoch then fields[#fields+1]=tostring(shotEpoch) end
  local arr={};for i,v in ipairs(fields) do arr[i]=enc(v) end
  local data=table.concat(arr,'|')
  NecroBugLocalBackup[#NecroBugLocalBackup+1]=data
  local rid=transport(data)
  if rid then
    f:Hide()
    -- No queued message: wait for the actual server receipt.
  end
end)
local pump=CreateFrame('Frame')
pump:RegisterEvent('CHAT_MSG_ADDON')
pump:SetScript('OnEvent',function(_,event,prefix,message,distribution)
  if event~='CHAT_MSG_ADDON' or prefix~='NECROBUG' or distribution~='WHISPER' then return end
  local rid,status,detail=message:match('^NBA3|([%d%-]+)|([A-Z]+)|([%w_%-]+)$')
  if not rid or not pending[rid] then return end
  pending[rid]=nil
  if status=='OK' then
    print('|cff00ff00NecroBug:|r Report received.')
  elseif status=='ERR' then
    print('|cffff4444NecroBug:|r Server could not save the report ('..detail..'). Local copy retained.')
  end
end)
pump:SetScript('OnUpdate',function(_,elapsed)
  timer=timer+elapsed
  if timer<0.25 then return end
  timer=0
  if #queue>0 then
    local chunk=table.remove(queue,1)
    -- Private addon transport consumed by worldserver before normal routing.
    C_ChatInfo.SendAddonMessage('NECROBUG',chunk.text,'WHISPER',UnitName('player'))
    if chunk.last and pending[chunk.rid] then pending[chunk.rid].sentAt=GetTime() end
  end
  for rid,item in pairs(pending) do
    if item.sentAt and GetTime()-item.sentAt>30 then
      pending[rid]=nil
      print('|cffffaa00NecroBug:|r No server confirmation received. Check dashboard before resubmitting. Local copy retained.')
    end
  end
end)
SLASH_NECROBUG1='/bug';SLASH_NECROBUG2='/necrobug';SlashCmdList.NECROBUG=function() open('Bug') end
SLASH_NECROIDEA1='/idea';SlashCmdList.NECROIDEA=function() open('Idea') end
choose('Bug')
print('|cff00ff00NecroBug:|r /bug opens Bugs; /idea opens Ideas.')
