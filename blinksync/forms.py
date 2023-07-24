import wx

DELETE = 1
CLOSE = 2
DOWNLOAD = 3
REFRESH = 4
DELAY = 5

class VideosForm(wx.Dialog):
    """My delete form."""
    def __init__(self,manifest):
        wx.Frame.__init__(self, None, wx.ID_ANY, "Select List to Download and Delete",size = (450,550))

        # Add a panel so it looks the correct on all platforms
        panel = wx.Panel(self, wx.ID_ANY)
        #self.Bind(wx.EVT,self._when_closed)
        self.index = 0
        self.ItemList = []
        self.list_ctrl = wx.ListCtrl(panel, size=(-1,400),
                        style=wx.LC_REPORT
                        |wx.BORDER_SUNKEN
                        )
        self.list_ctrl.InsertColumn(0, 'Name')
        self.list_ctrl.InsertColumn(1, 'Camera')
        self.list_ctrl.InsertColumn(2, 'Date', width=225)
        self.list_ctrl.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK,self.download_line)

        btn = wx.Button(panel, label="Download")
        btn.Bind(wx.EVT_BUTTON, self.download_line)

        deletebtn = wx.Button(panel, label="Delete")
        deletebtn.Bind(wx.EVT_BUTTON, self.delete_line)

        closeBtn = wx.Button(panel, label="Close")
        closeBtn.Bind(wx.EVT_BUTTON, self._when_closed)

        refrestBtn = wx.Button(panel, label="Refresh")
        refrestBtn.Bind(wx.EVT_BUTTON, self._refresh)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.list_ctrl, 0, wx.ALL|wx.EXPAND, 20)
        sizer_buttons = wx.BoxSizer(wx.HORIZONTAL)
        sizer_buttons.Add(btn, 0, wx.ALL|wx.CENTER, 5)
        sizer_buttons.Add(deletebtn,0,wx.ALL|wx.CENTER,5)
        sizer_buttons.Add(refrestBtn,0,wx.ALL|wx.CENTER,5)
        sizer_buttons.Add(closeBtn,0,wx.ALL|wx.CENTER, 5)
        sizer.Add(sizer_buttons,0,wx.ALL|wx.CENTER,5)
        panel.SetSizer(sizer)

        for item in reversed(manifest):
            self.list_ctrl.InsertItem(self.index, str(item.id))
            self.list_ctrl.SetItem(self.index, 1, item.name)
            self.list_ctrl.SetItem(self.index, 2, item.created_at.astimezone().isoformat())
            self.index += 1
    #----------------------------------------------------------------------
    def download_line(self, event):
        """Add to list and return DOWNLOAD"""
        for count in range(self.list_ctrl.ItemCount):
            if self.list_ctrl.IsSelected(count):
                self.ItemList.append(int(self.list_ctrl.GetItem(count).Text))
        self.EndModal(DOWNLOAD)

    def delete_line(self, event):
        """Add to list and return DOWNLOAD"""
        for count in range(self.list_ctrl.ItemCount):
            if self.list_ctrl.IsSelected(count):
                self.ItemList.append(int(self.list_ctrl.GetItem(count).Text))
        self.EndModal(DELETE)


    def _when_closed(self,event):
        self.EndModal(CLOSE)

    def _refresh(self,event):
        self.EndModal(REFRESH)

class LoginDialog(wx.Dialog):
    """
    Class to define login dialog
    """
    #----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""
        wx.Dialog.__init__(self, None, title="Login")

        # user info
        user_sizer = wx.BoxSizer(wx.HORIZONTAL)

        user_lbl = wx.StaticText(self, label="Username:")
        user_sizer.Add(user_lbl, 0, wx.ALL|wx.CENTER, 5)
        self.user = wx.TextCtrl(self)
        user_sizer.Add(self.user, 0, wx.ALL, 5)

        # pass info
        p_sizer = wx.BoxSizer(wx.HORIZONTAL)

        p_lbl = wx.StaticText(self, label="Password:")
        p_sizer.Add(p_lbl, 0, wx.ALL|wx.CENTER, 5)
        self.password = wx.TextCtrl(self, style=wx.TE_PASSWORD|wx.TE_PROCESS_ENTER)
        p_sizer.Add(self.password, 0, wx.ALL, 5)

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(user_sizer, 0, wx.ALL, 5)
        main_sizer.Add(p_sizer, 0, wx.ALL, 5)

        btn = wx.Button(self, label="Login")
        btn.Bind(wx.EVT_BUTTON, self.onLogin)
        main_sizer.Add(btn, 0, wx.ALL|wx.CENTER, 5)

        self.SetSizer(main_sizer)

    #----------------------------------------------------------------------
    def onLogin(self, event):
        """
        Check credentials and login
        """
        self.account = {"username":self.user.Value,"password":self.password.Value}
        self.EndModal(wx.ID_OK) 

    def getUserPassword(self):
        return self.account

