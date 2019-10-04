#!/usr/bin/env python3

# This file is part of Openplotter.
# Copyright (C) 2019 by Sailoog <https://github.com/openplotter/openplotter-can>
#                     
# Openplotter is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# any later version.
# Openplotter is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Openplotter. If not, see <http://www.gnu.org/licenses/>.

import wx, os, webbrowser, subprocess, socket, ujson
import wx.richtext as rt
from openplotterSettings import conf
from openplotterSettings import language
from openplotterSettings import platform

import wx, time, serial, codecs
from wx.lib.mixins.listctrl import CheckListCtrlMixin, ListCtrlAutoWidthMixin

class MyFrame(wx.Frame):
	def __init__(self):
		self.conf = conf.Conf()
		self.conf_folder = self.conf.conf_folder
		self.platform = platform.Platform()
		self.currentdir = os.path.dirname(__file__)
		self.currentLanguage = self.conf.get('GENERAL', 'lang')
		self.language = language.Language(self.currentdir,'openplotter-can',self.currentLanguage)

		wx.Frame.__init__(self, None, title=_('OpenPlotter CAN'), size=(800,444))
		self.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
		icon = wx.Icon(self.currentdir+"/data/openplotter-can.png", wx.BITMAP_TYPE_PNG)
		self.SetIcon(icon)
		self.CreateStatusBar()
		font_statusBar = self.GetStatusBar().GetFont()
		font_statusBar.SetWeight(wx.BOLD)
		self.GetStatusBar().SetFont(font_statusBar)

		self.toolbar1 = wx.ToolBar(self, style=wx.TB_TEXT)
		toolHelp = self.toolbar1.AddTool(101, _('Help'), wx.Bitmap(self.currentdir+"/data/help.png"))
		self.Bind(wx.EVT_TOOL, self.OnToolHelp, toolHelp)
		if not self.platform.isInstalled('openplotter-doc'): self.toolbar1.EnableTool(101,False)
		toolSettings = self.toolbar1.AddTool(102, _('Settings'), wx.Bitmap(self.currentdir+"/data/settings.png"))
		self.Bind(wx.EVT_TOOL, self.OnToolSettings, toolSettings)
		self.toolbar1.AddSeparator()
		self.canUsbSetup = self.toolbar1.AddTool(103, _('CAN-USB Setup'), wx.Bitmap(self.currentdir+"/data/openplotter-24.png"))
		self.Bind(wx.EVT_TOOL, self.onCanUsbSetup, self.canUsbSetup)
		self.toolbar1.AddSeparator()
		self.AddSkCon = self.toolbar1.AddTool(104, _('SK connections'), wx.Bitmap(self.currentdir+"/data/sk.png"))
		self.Bind(wx.EVT_TOOL, self.onAddSkCon, self.AddSkCon)
		self.SKtoN2K = self.toolbar1.AddTool(105, _('SK Output'), wx.Bitmap(self.currentdir+"/data/sk.png"))
		self.Bind(wx.EVT_TOOL, self.onSKtoN2K, self.SKtoN2K)
		self.toolbar1.AddSeparator()
		toolApply = self.toolbar1.AddTool(106, _('Apply'), wx.Bitmap(self.currentdir+"/data/apply.png"))
		self.Bind(wx.EVT_TOOL, self.OnToolApply, toolApply)
		toolCancel = self.toolbar1.AddTool(107, _('Cancel'), wx.Bitmap(self.currentdir+"/data/cancel.png"))
		self.Bind(wx.EVT_TOOL, self.OnToolCancel, toolCancel)

		self.notebook = wx.Notebook(self)
		self.notebook.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.onTabChange)
		self.sk = wx.Panel(self.notebook)
		self.op = wx.Panel(self.notebook)
		self.mcp2515 = wx.Panel(self.notebook)
		self.notebook.AddPage(self.sk, _('CAN-USB'))
		self.notebook.AddPage(self.op, _('CAN-USB / CANable'))
		self.notebook.AddPage(self.mcp2515, _('MCP2515'))
		self.il = wx.ImageList(24, 24)
		img0 = self.il.Add(wx.Bitmap(self.currentdir+"/data/openplotter-24.png", wx.BITMAP_TYPE_PNG))
		img1 = self.il.Add(wx.Bitmap(self.currentdir+"/data/openplotter-24.png", wx.BITMAP_TYPE_PNG))
		img2 = self.il.Add(wx.Bitmap(self.currentdir+"/data/chip.png", wx.BITMAP_TYPE_PNG))
		self.notebook.AssignImageList(self.il)
		self.notebook.SetPageImage(0, img0)
		self.notebook.SetPageImage(1, img1)
		self.notebook.SetPageImage(2, img2)

		vbox = wx.BoxSizer(wx.VERTICAL)
		vbox.Add(self.toolbar1, 0, wx.EXPAND)
		vbox.Add(self.notebook, 1, wx.EXPAND)
		self.SetSizer(vbox)

		self.pageSk()
		self.pageOp()
		self.pageMcp2515()

		maxi = self.conf.get('GENERAL', 'maximize')
		if maxi == '1': self.Maximize()

		self.Centre() 

	def ShowStatusBar(self, w_msg, colour):
		self.GetStatusBar().SetForegroundColour(colour)
		self.SetStatusText(w_msg)

	def ShowStatusBarRED(self, w_msg):
		self.ShowStatusBar(w_msg, (130,0,0))

	def ShowStatusBarGREEN(self, w_msg):
		self.ShowStatusBar(w_msg, (0,130,0))

	def ShowStatusBarBLACK(self, w_msg):
		self.ShowStatusBar(w_msg, wx.BLACK) 

	def ShowStatusBarYELLOW(self, w_msg):
		self.ShowStatusBar(w_msg,(255,140,0)) 

	def onTabChange(self, event):
		self.SetStatusText('')
		if self.notebook.GetSelection() == 1 or self.notebook.GetSelection() == 2:
			self.toolbar1.EnableTool(106,True)
			self.toolbar1.EnableTool(107,True)
		else:
			self.toolbar1.EnableTool(106,False)
			self.toolbar1.EnableTool(107,False)

	def OnToolHelp(self, event): 
		url = "/usr/share/openplotter-doc/can/can_app.html"
		webbrowser.open(url, new=2)

	def OnToolSettings(self, event=0): 
		subprocess.call(['pkill', '-f', 'openplotter-settings'])
		subprocess.Popen('openplotter-settings')

	def pageMcp2515(self):
		pass

	def pageSk(self):
		skLabel = wx.StaticText(self.sk, label='Actinsense NGT-1 (canboatjs)')
		self.listSKcan = wx.ListCtrl(self.sk, -1, style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.LC_HRULES, size=(-1,200))
		self.listSKcan.InsertColumn(0, _('ID'), width=200)
		self.listSKcan.InsertColumn(1, _('Serial Port'), width=200)
		self.listSKcan.InsertColumn(2, _('Baud Rate'), width=200)
		self.listSKcan.Bind(wx.EVT_LIST_ITEM_SELECTED, self.onListSKcanSelected)
		self.listSKcan.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.onListSKcanDeselected)

		self.toolbar2 = wx.ToolBar(self.sk, style=wx.TB_TEXT | wx.TB_VERTICAL)
		self.editSkCon = self.toolbar2.AddTool(201, _('Edit Connection'), wx.Bitmap(self.currentdir+"/data/sk.png"))
		self.Bind(wx.EVT_TOOL, self.onEditSkCon, self.editSkCon)
		self.RefreshSk = self.toolbar2.AddTool(202, _('Refresh'), wx.Bitmap(self.currentdir+"/data/refresh.png"))
		self.Bind(wx.EVT_TOOL, self.onRefreshSk, self.RefreshSk)
		self.toolbar2.AddSeparator()
		self.SKcanTX = self.toolbar2.AddTool(203, _('Open device TX PGNs'), wx.Bitmap(self.currentdir+"/data/openplotter-24.png"))
		self.Bind(wx.EVT_TOOL, self.onSKcanTX, self.SKcanTX)

		h1 = wx.BoxSizer(wx.VERTICAL)
		h1.AddSpacer(5)
		h1.Add(skLabel, 0, wx.LEFT, 10)
		h1.AddSpacer(5)
		h1.Add(self.listSKcan, 1, wx.EXPAND, 0)

		sizer = wx.BoxSizer(wx.HORIZONTAL)
		sizer.Add(h1, 1, wx.EXPAND, 0)
		sizer.Add(self.toolbar2, 0)
		self.sk.SetSizer(sizer)

		self.readSk()

	def readSk(self):
		self.sklist = []
		try:
			setting_file = self.platform.skDir+'/settings.json'
			data = ''
			with open(setting_file) as data_file:
				data = ujson.load(data_file)
			if 'pipedProviders' in data:
				for i in data['pipedProviders']:
					if i['pipeElements'][0]['options']['subOptions']['type']=='ngt-1-canboatjs':
						self.sklist.append([i['id'],i['pipeElements'][0]['options']['subOptions']['device'],i['pipeElements'][0]['options']['subOptions']['baudrate'],i['enabled']])
		except:pass

		self.listSKcan.DeleteAllItems()
		for ii in self.sklist:
			self.listSKcan.Append([ii[0],ii[1],str(ii[2])])
			if ii[3]: self.listSKcan.SetItemBackgroundColour(self.listSKcan.GetItemCount()-1,(0,191,255))

		selected = self.listSKcan.GetFirstSelected()
		if selected == -1:
			self.toolbar2.EnableTool(201,False)
			self.toolbar2.EnableTool(203,False)
		else:
			self.toolbar2.EnableTool(201,True)
			self.toolbar2.EnableTool(203,True)

	def onCanUsbSetup(self,e):
		subprocess.call(['pkill', '-15', 'CAN-USB-firmware'])
		subprocess.call(['x-terminal-emulator','-e', 'CAN-USB-firmware'])

	def onAddSkCon(self,e):
		if self.platform.skPort: 
			url = self.platform.http+'localhost:'+self.platform.skPort+'/admin/#/serverConfiguration/connections/-'
			webbrowser.open(url, new=2)
		else: 
			self.ShowStatusBarRED(_('Please install "Signal K Installer" OpenPlotter app'))
			self.OnToolSettings()

	def onSKtoN2K(self,e):
		if self.platform.skPort: 
			if self.platform.isSKpluginInstalled('signalk-to-nmea2000'):
				url = self.platform.http+'localhost:'+self.platform.skPort+'/admin/#/serverConfiguration/plugins/sk-to-nmea2000'
			else: 
				self.ShowStatusBarRED(_('Please install "signalk-to-nmea2000" signal K app'))
				url = self.platform.http+'localhost:'+self.platform.skPort+'/admin/#/appstore/apps'
			webbrowser.open(url, new=2)
		else: 
			self.ShowStatusBarRED(_('Please install "Signal K Installer" OpenPlotter app'))
			self.OnToolSettings()

	def onEditSkCon(self,e):
		selected = self.listSKcan.GetFirstSelected()
		if selected == -1: return
		skId = self.listSKcan.GetItemText(selected, 0)
		url = self.platform.http+'localhost:'+self.platform.skPort+'/admin/#/serverConfiguration/connections/'+skId
		webbrowser.open(url, new=2)

	def onRefreshSk(self,e):
		self.readSk()

	def onSKcanTX(self,e):
		selected = self.listSKcan.GetFirstSelected()
		if selected == -1: return
		skId = self.listSKcan.GetItemText(selected, 0)
		device = self.listSKcan.GetItemText(selected, 1)
		bauds = self.listSKcan.GetItemText(selected, 2)
		if self.enable_disable_device(skId,0): self.restart_SK(_('Disabling device and restarting Signal K server... '))
		dlg = openPGNs(self,device,bauds)
		res = dlg.ShowModal()
		dlg.Destroy()
		if self.enable_disable_device(skId,1): self.restart_SK(_('Enabling device and restarting Signal K server... '))

	def enable_disable_device(self,deviceId,enable):
		write = False
		try:
			count = 0
			setting_file = self.platform.skDir+'/settings.json'
			data = ''
			with open(setting_file) as data_file:
				data = ujson.load(data_file)
			for i in data['pipedProviders']:
				if i['id'] == deviceId:
					if enable == 1:
						if i['enabled'] == False:
							write = True
							data['pipedProviders'][count]['enabled'] = True
					elif enable == 0:
						if i['enabled'] == True:
							write = True
							data['pipedProviders'][count]['enabled'] = False
				count = count + 1
			if write:
				data2 = ujson.dumps(data, indent=4, sort_keys=True)
				file = open(setting_file, 'w')
				file.write(data2)
				file.close()
		except: pass

		return write
		
	def restart_SK(self, msg):
		if msg == 0: msg = _('Restarting Signal K server... ')
		seconds = 12
		subprocess.Popen([self.platform.admin, 'python3', self.currentdir+'/service.py', 'stop'])
		subprocess.Popen([self.platform.admin, 'python3', self.currentdir+'/service.py', 'start'])
		for i in range(seconds, 0, -1):
			self.ShowStatusBarYELLOW(msg+str(i))
			time.sleep(1)
		self.ShowStatusBarGREEN(_('Signal K server restarted'))
		self.readSk()


	def onListSKcanSelected(self,e):
		i = e.GetIndex()
		valid = e and i >= 0
		if not valid: return
		self.toolbar2.EnableTool(201,True)
		self.toolbar2.EnableTool(203,True)

	def onListSKcanDeselected(self,e):
		self.toolbar2.EnableTool(201,False)
		self.toolbar2.EnableTool(203,False)

	def pageOp(self):
		pass

	def OnToolApply(self,e):
		pass
		
	def OnToolCancel(self,e):
		pass

################################################################################

class CheckListCtrl(wx.ListCtrl, CheckListCtrlMixin, ListCtrlAutoWidthMixin):
	def __init__(self, parent, width,height):
		wx.ListCtrl.__init__(self, parent, -1, style=wx.LC_REPORT, size=(width, height))
		CheckListCtrlMixin.__init__(self)
		ListCtrlAutoWidthMixin.__init__(self)

class openPGNs(wx.Dialog):

	def __init__(self,parent,alias,bauds):
		self.error = ''
		self.can_device = alias
		self.baud_ = bauds
		self.parent = parent
		self.conf = parent.conf
		self.currentpath = parent.currentdir
		self.ttimer = 100
		Buf_ = bytearray(128)
		self.Buffer = bytearray(Buf_)
		self.Zustand=6
		self.buffer=0
		self.PGN_list=[]
		self.list_N2K_txt=[]
		self.list_count=[]
		self.p=0

		wx.Dialog.__init__(self, None, title=_('Open device PGNs'), size=(650,430))
		self.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))

		self.timer = wx.Timer(self)
		self.Bind(wx.EVT_TIMER, self.timer_act, self.timer)

		panel = wx.Panel(self, 100)
		self.list_N2K = CheckListCtrl(panel, -1,240)
		self.list_N2K.SetBackgroundColour((230,230,230))
		self.list_N2K.SetPosition((10, 25))
		self.list_N2K.InsertColumn(0, _('TX PGN'), width=100)
		self.list_N2K.InsertColumn(1, _('info'), width=220)
		self.txLabel = wx.StaticText(panel, wx.ID_ANY, style=wx.ALIGN_CENTER)
		self.printing = wx.TextCtrl(panel, -1, style=wx.TE_MULTILINE | wx.TE_READONLY, size=(-1,50))
		self.printing.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_INACTIVECAPTION))

		apply_b = wx.Button(panel, label=_('Apply'))
		self.Bind(wx.EVT_BUTTON, self.apply, apply_b)
		close_b = wx.Button(panel, label=_('Close'))
		self.Bind(wx.EVT_BUTTON, self.OnClose, close_b)

		hbox = wx.BoxSizer(wx.HORIZONTAL)
		hbox.AddStretchSpacer(1)
		hbox.Add(apply_b, 0, wx.LEFT, 10)
		hbox.Add(close_b, 0, wx.LEFT, 10)

		vbox = wx.BoxSizer(wx.VERTICAL)
		vbox.Add(self.list_N2K, 1, wx.ALL | wx.EXPAND, 10)
		vbox.Add(self.txLabel, 0, wx.LEFT, 10)
		vbox.Add(self.printing, 1, wx.ALL | wx.EXPAND, 10)
		vbox.Add(hbox, 1, wx.ALL | wx.EXPAND, 10)

		panel.SetSizer(vbox)
		self.Centre()

		try:
			self.ser = serial.Serial(self.can_device, self.baud_, timeout=0.5)
		except:
			self.printing.SetValue(_('Error connecting with device ')+self.can_device)
			apply_b.Disable()
			self.list_N2K.Disable()
		else:
			self.read_N2K()
			self.check(0)
			self.timer.Start(self.ttimer)

	def check(self,e):
		self.printing.SetValue('')
		i=0
		self.work = True
		while (self.work):
			self.getCharfromSerial()
			time.sleep(0.01)
			i+=1
			if i>20:
				self.work = False

		self.Send_Command(1, 0x01, 0)
		time.sleep(0.2)

		counter=0
		for ii in self.list_N2K_txt:
			self.list_N2K.CheckItem(counter,False)
			counter+=1

		self.PGN_list=[]
		self.work = True
		self.Send_Command(1, 0x49, 0)
		i=0
		while (self.work):
			self.getCharfromSerial()
			time.sleep(0.01)
			i+=1
			if i>200:
				self.work = False
		self.read_stick_check()
		if len(self.PGN_list)<1: self.printing.SetValue(_('The list of enabled PGNs is empty, you may need to try a different baudrate or reset your device to 115200 bauds'))

	def apply(self,e):
		new = _('open PGNs: ')
		close = _('close PGNs: ')
		msg = ''
		counter = 0
		maxpgns = False
		st=''
		for ii in self.list_N2K_txt:
			if self.list_N2K.IsChecked(counter):
				exist=0
				for jj in self.PGN_list:
					if ii[0]==str(jj):
						exist=1
				if exist==0:
					st+=ii[0]+' '
					if len(self.PGN_list)<30:
						self.sendTX_PGN(int(ii[0]),1)
						self.PGN_list.append(ii[0])
						time.sleep(0.2)
					else: maxpgns = True
			counter+=1
		new += st

		st=''
		for jj in self.PGN_list:
			counter=0
			for ii in self.list_N2K_txt:
				exist=0
				if ii[0]==str(jj):
					if not self.list_N2K.IsChecked(counter):
						exist=1
					if exist==1:
						st+=ii[0]+' '
						self.sendTX_PGN(int(ii[0]),0)
						time.sleep(0.2)
				counter+=1
		close += st

		self.Send_Command(1, 0x01, 0)
		if maxpgns: msg += _('You can not activate more than 30 PGNs\n\n')
		msg += new+'\n'+close
		wx.MessageBox(msg, 'Info', wx.OK | wx.ICON_INFORMATION)
		self.check(0)

	def sendTX_PGN(self,lPGN,add):
		if add:
			data_ = (0,0,0,0,1,0xFE,0xFF,0xFF,0xFF,0xFE,0xFF,0xFF,0xFF)
			data = bytearray(data_)
		else:
			data = bytearray(13)
		data[0]=lPGN&255
		data[1]=(lPGN >> 8)&255
		data[2]=(lPGN >> 16)&255

		self.Send_Command(14, 0x47, data)

	def Send_Command(self, length, command, arg):
		data = bytearray(length+3)
		
		data[0] = 0xa1 #command
		data[1] = length #Actisense length
		data[2] = command
		i=3
		while i<length+2:
			data[i] = arg[i-3]
			i+=1
		self.SendCommandtoSerial(data)

	def timer_act(self,e):
		self.getCharfromSerial()

	def OnClose(self, event):
		self.timer.Stop()
		self.EndModal(wx.OK)

	def SendCommandtoSerial(self, TXs):
		crc = 0
		i = 0
		while i < TXs[1] + 2:
			crc += TXs[i]
			i += 1
		crc = (256 - crc) & 255
		TXs[TXs[1] + 2] = crc

		TYs = b''
		while i < TXs[1] + 3:
			TYs = TYs+bytes(TXs[i])
			if TXs[i] == 0x10:
				TYs = TYs+bytes(TXs[i])
			i += 1		
		start = b'\x10\x02'
		ende = b'\x10\x03'
		self.ser.write(start+TXs+ende)

	def getCharfromSerial(self):
		bytesToRead = self.ser.inWaiting()
		if bytesToRead>0:
			buffer=self.ser.read(bytesToRead)
			for i in buffer:
				self.parse(i)			

	def parse(self, b):
		if self.Zustand == 6: # zu Beginn auf 0x10 warten
			if b == 0x10:
				self.Zustand = 0x10
		elif self.Zustand == 0x10:
			if b == 0x10: # 0x10 Schreiben wenn zweimal hintereinander
				self.Buffer[self.p] = b
				self.p += 1
				self.Zustand = 0
			elif b == 0x02: # Anfang gefunden
				self.p = 0
				self.Zustand = 0
			elif b == 0x03: # Ende gefunden
				if self.crcCheck():
					self.output()
				self.p = 0
				self.Zustand = 6 # Auf Anfang zuruecksetzen
		elif self.Zustand == 0:
			if b == 0x10:
				self.Zustand = 0x10
			else:
				self.Buffer[self.p] = b
				self.p += 1

	def crcCheck(self):
		crc = 0
		i = 0
		while i < self.p:
			crc =(crc+ self.Buffer[i]) & 255
			i += 1
		return (crc == 0)

	def output(self):
		if self.Buffer[0] == 0x93 and self.Buffer[1] == self.p - 3:
			pass
		else:
			if self.Buffer[2] == 0x49 and self.Buffer[3] == 0x01:
				j = 0
				st=''
				self.PGN_list=[]
				while j < self.Buffer[14]:
					i=j*4
					lPGN=self.Buffer[15+i]+self.Buffer[16+i]*256+self.Buffer[17+i]*256*256
					if lPGN in self.PGN_list:
						print(lPGN,'already exists')
					else:
						self.PGN_list.append(lPGN)
						st+=str(lPGN)+' '

					j+=1
				self.printing.SetValue(st)
				self.txLabel.SetLabel(str(j)+_(" enabled transmission PGNs (max. 30):"))
				self.work = False

	def read_N2K(self):
		if self.list_N2K.GetItemCount()<3:
			while self.list_N2K.GetItemCount()>3:
				self.list_N2K.DeleteItem(self.list_N2K.GetItemCount()-1)

			self.list_N2K_txt=[]
			with open(self.currentpath+'/data/N2K_PGN.csv') as f:
				self.list_N2K_txt = [x.strip('\n\r').split(',') for x in f.readlines()]

			for ii in self.list_N2K_txt:
				pgn=int(ii[0])
				self.list_N2K.Append([pgn,ii[1]])

	def read_stick_check(self):
		counter=0
		self.list_N2K.CheckItem(0,False)
		for ii in self.list_N2K_txt:
			for jj in self.PGN_list:
				if ii[0]==str(jj):
					self.list_N2K.CheckItem(counter)
			counter+=1
		self.list_N2K.Update()

################################################################################

def main():
	app = wx.App()
	MyFrame().Show()
	app.MainLoop()

if __name__ == '__main__':
	main()