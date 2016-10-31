#Embedded file name: /usr/lib/enigma2/python/Plugins/Extensions/BhPersonalBackup/plugin.py
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.ScrollLabel import ScrollLabel
from Components.Pixmap import Pixmap, MultiPixmap
from Plugins.Plugin import PluginDescriptor
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Tools.Directories import fileExists
from Components.ConfigList import ConfigListScreen
from Components.config import getConfigListEntry, config, ConfigYesNo, ConfigSelection, NoSave, configfile
from os import system, listdir, chdir, getcwd, rename as os_rename, remove as os_remove
from os.path import dirname, isdir
from enigma import eTimer

class Bh_Bpersonal_main(Screen):
    skin = '\n\t\t<screen position="center,center" size="710,340" title="Black Hole Personal Backup" >\n\t\t\t<widget name="lab1" position="20,20" size="680,64" font="Regular;24" valign="center" transparent="1"/>\n\t\t\t<ePixmap pixmap="skin_default/buttons/red.png" position="72,290" size="140,40" alphatest="on" />\n\t\t\t<ePixmap pixmap="skin_default/buttons/green.png" position="284,290" size="140,40" alphatest="on" />\n\t\t\t<ePixmap pixmap="skin_default/buttons/yellow.png" position="495,290" size="140,40" alphatest="on" />\n\t\t\t<widget name="key_red" position="72,290" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" />\n\t\t\t<widget name="key_green" position="284,290" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />\n\t\t\t<widget name="key_yellow" position="495,290" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="yellow" transparent="1" />\n\t\t</screen>\n\t\t'

    def __init__(self, session, args = None):
        Screen.__init__(self, session)
        self['lab1'] = Label(_('Personal Backup: not found.'))
        self['key_red'] = Label(_('Backup'))
        self['key_green'] = Label(_('Restore'))
        self['key_yellow'] = Label(_('Setup'))
        self['actions'] = ActionMap(['OkCancelActions', 'ColorActions'], {'cancel': self.close,
         'red': self.backuP,
         'green': self.restorE,
         'yellow': self.setuP}, -1)
        self.onLayoutFinish.append(self.updateT)

    def updateT(self):
        self.mybackupfile = ''
        mytext = _('Personal Backup: not found.')
        myfile = ''
        if fileExists('/etc/bhpersonalbackup'):
            f = open('/etc/bhpersonalbackup', 'r')
            mypath = f.readline().strip()
            f.close()
            myt = mypath + 'BhPersonalBackup.bh4'
            if fileExists(myt):
                myfile = myt
            myt = mypath + 'BhPersonalBackup.bh5'
            if fileExists(myt):
                myfile = myt
        if myfile == '':
            myfile = self.scan_mediA()
        if myfile == '':
            myfile = self.scan_deV()
        if myfile.find('.bh4') != -1:
            mytext = _('Sorry. Personal Backup found but due to structural changes it is not compatible with the new image version')
        if myfile.find('.bh5') != -1:
            mytext = _('Personal Backup found: ') + myfile
            self.mybackupfile = myfile
        self['lab1'].setText(mytext)

    def scan_deV(self):
        if isdir('/dev/disk/by-uuid/') == True:
            system('mkdir /media/bhbackuptmp')
            pkgs = listdir('/dev/disk/by-uuid/')
            myfile = '/media/bhbackuptmp/BhPersonalBackup.bh5'
            myfile2 = '/media/bhbackuptmp/BhPersonalBackup.bh4'
            for device in pkgs:
                cmd = 'mount /dev/disk/by-uuid/' + device + ' /media/bhbackuptmp'
                rc = system(cmd)
                if fileExists(myfile):
                    return myfile
                if fileExists(myfile2):
                    system('umount /media/bhbackuptmp')
                    return myfile2
                system('umount /media/bhbackuptmp')

        return ''

    def scan_mediA(self):
        mylist = ['/media/hdd',
         '/media/cf',
         '/media/card',
         '/media/usb',
         '/media/usb2',
         '/media/usb3',
         '/media/net']
        for fil in mylist:
            myfile = fil + '/BhPersonalBackup.bh5'
            if fileExists(myfile):
                return myfile
            myfile = fil + '/BhPersonalBackup.bh4'
            if fileExists(myfile):
                return myfile

        return ''

    def setuP(self):
        check = False
        if fileExists('/proc/mounts'):
            f = open('/proc/mounts', 'r')
            for line in f.readlines():
                if line.find('/media/cf') != -1:
                    check = True
                elif line.find('/media/usb') != -1:
                    check = True
                elif line.find('/media/card') != -1:
                    check = True
                elif line.find('/hdd') != -1:
                    check = True

            f.close()
        if check == False:
            self.session.open(MessageBox, _('Sorry no device found to store backup.'), MessageBox.TYPE_INFO)
        else:
            self.session.openWithCallback(self.updateT, Bh_Bpersonal_setuP)

    def restorE(self):
        if self.mybackupfile != '':
            message = _('Do you really want to restore the Backup:\n ') + self.mybackupfile + ' ?'
            self.session.openWithCallback(self.restorE_2, MessageBox, message, MessageBox.TYPE_YESNO)
        else:
            system('umount /media/bhbackuptmp')
            system('rmdir /media/bhbackuptmp')
            self.session.open(MessageBox, _('Sorry Personal Backup not found.'), MessageBox.TYPE_INFO)

    def restorE_2(self, answer):
        if answer is True:
            tmppath = dirname(self.mybackupfile)
            self.session.open(Bh_Bpersonal_restorePreF, tmppath)

    def backuP(self):
        if fileExists('/etc/bhpersonalbackup'):
            self.session.openWithCallback(self.updateT, Bh_Bpersonal_baK)
        else:
            self.session.open(MessageBox, _('You have to setup backup location.'), MessageBox.TYPE_INFO)


class Bh_Bpersonal_restorePreF(Screen, ConfigListScreen):
    skin = '\n\t<screen position="center,center" size="902,550" title="Black Hole Restore Preferences">\n\t\t<widget name="config" position="30,10" size="840,510" scrollbarMode="showOnDemand"/>\n\t\t<ePixmap pixmap="skin_default/buttons/red.png" position="380,510" size="140,40" alphatest="on"/>\n\t\t<widget name="key_red" position="380,510" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1"/>\n\t</screen>'

    def __init__(self, session, mypath):
        Screen.__init__(self, session)
        self.mypath = mypath
        self.list = []
        ConfigListScreen.__init__(self, self.list)
        self['key_red'] = Label(_('Continue'))
        self['actions'] = ActionMap(['WizardActions', 'ColorActions'], {'red': self.Continue,
         'ok': self.Continue})
        self.updateList()

    def updateList(self):
        blist = ['Password',
         'Devices',
         'Network config',
         'Cron',
         'Swap',
         'Keymaps',
         'Openvpn',
         'Inadyn',
         'Uninstall files',
         'Settings Channels Bouquets',
         'Satellites Terrestrial',
         'Epg channels',
         'Cams',
         'Scripts',
         'Bootlogo',
         'Plugins Extensions',
         'System Plugins']
        for x in blist:
            item = NoSave(ConfigYesNo(default=True))
            item2 = getConfigListEntry(x, item)
            self.list.append(item2)

        self['config'].list = self.list
        self['config'].l.setList(self.list)

    def Continue(self):
        mylist = ['start',
         'extract',
         'usr/lib',
         'usr/bin',
         'etc']
        for x in self['config'].list:
            if x[1].value == True:
                mylist.append(x[0])

        mylist.append('END')
        self.session.open(Bh_Bpersonal_restoreDo, self.mypath, mylist)
        self.close()


class Bh_Bpersonal_restoreDo(Screen):
    skin = '\n\t\t<screen position="center,center" size="1000,500" title="Black Hole Personal Restore" >\n\t\t\t<widget name="lab1" position="10,10" size="980,480" font="Regular;22" />\n\t\t</screen>\n\t\t'

    def __init__(self, session, mypath, mylist):
        Screen.__init__(self, session)
        self.mytext = _('Files extraction in progress...\n\n')
        self['lab1'] = ScrollLabel(self.mytext)
        self.mypath = mypath + '/bhbackuptmp2'
        self.mybackupfile = mypath + '/BhPersonalBackup.bh5'
        self.mylist = mylist
        self.count = 0
        self.go = False
        self['actions'] = ActionMap(['OkCancelActions', 'ColorActions', 'DirectionActions'], {'ok': self.hrestBox,
         'up': self['lab1'].pageUp,
         'down': self['lab1'].pageDown})
        self.activityTimer = eTimer()
        self.activityTimer.timeout.get().append(self.updatepix)
        self.procesS()

    def updatepix(self):
        self.activityTimer.stop()
        self['lab1'].setText(self.mytext)
        self.procesS()

    def procesS(self):
        cur = self.mylist[self.count]
        if cur == 'start':
            self.mytext += _('Archive Extraction\t\t\t') + ' [ OK ]\n'
        if cur == 'extract':
            system('mkdir ' + self.mypath)
            mydir = getcwd()
            chdir(self.mypath)
            cmd = 'tar -xf ' + self.mybackupfile
            rc = system(cmd)
            chdir(mydir)
            ret = system('rm ' + self.mypath + '/etc/enigma2/skin_user.xml')
        elif cur == 'usr/lib':
            self.mytext += _('Merge directory ') + cur + '\t\t\t' + ' [ OK ]\n'
            ret = self.mergediR('/usr/lib')
        elif cur == 'usr/bin':
            self.mytext += _('Merge directory ') + cur + '\t\t\t' + ' [ OK ]\n'
            ret = self.mergediR('/usr/bin')
        elif cur == 'etc':
            self.mytext += _('Merge directory ') + cur + '\t\t\t' + ' [ OK ]\n'
            ret = self.mergediR('/etc')
            ret = self.mergediR('/etc/rc3.d')
        elif cur == 'Password':
            self.mytext += _('Restore ') + cur + '\t\t\t' + ' [ OK ]\n'
            ret = system('cp -f ' + self.mypath + '/etc/passwd /etc/')
        elif cur == 'Devices':
            self.mytext += _('Restore ') + cur + '\t\t\t' + ' [ OK ]\n'
            ret = system('cp -f ' + self.mypath + '/usr/bin/bhmount /usr/bin/')
        elif cur == 'Network config':
            self.mytext += _('Restore ') + cur + '\t\t\t' + ' [ OK ]\n'
            ret = system('cp -f ' + self.mypath + '/etc/resolv.conf /etc/')
            ret = system('cp -f ' + self.mypath + '/etc/wpa_supplicant.conf /etc/')
            ret = system('cp -f ' + self.mypath + '/etc/network/interfaces /etc/network/')
        elif cur == 'Cron':
            self.mytext += _('Restore ') + cur + '\t\t\t\t' + ' [ OK ]\n'
            ret = system('cp -rf ' + self.mypath + '/etc/bhcron /etc/')
        elif cur == 'Swap':
            self.mytext += _('Restore ') + cur + '\t\t\t\t' + ' [ OK ]\n'
            ret = system('cp -f ' + self.mypath + '/usr/bin/.Bhautoswap /usr/bin/')
        elif cur == 'Keymaps':
            self.mytext += _('Restore ') + cur + '\t\t\t' + ' [ OK ]\n'
        elif cur == 'Openvpn':
            self.mytext += _('Restore ') + cur + '\t\t\t' + ' [ OK ]\n'
            ret = system('cp -f ' + self.mypath + '/usr/bin/openvpn_script.sh /usr/bin/')
            ret = system('cp -rf ' + self.mypath + '/etc/openvpn /etc/')
        elif cur == 'Inadyn':
            self.mytext += _('Restore ') + cur + '\t\t\t\t' + ' [ OK ]\n'
            ret = system('cp -f ' + self.mypath + '/usr/bin/inadyn_script.sh /usr/bin/')
        elif cur == 'Uninstall files':
            self.mytext += _('Restore ') + cur + '\t\t\t' + ' [ OK ]\n'
            ret = system('cp -rf ' + self.mypath + '/usr/uninstall /usr/')
        elif cur == 'Settings Channels Bouquets':
            self.mytext += _('Restore ') + cur + '\t\t' + ' [ OK ]\n'
            ret = system('cp -rf ' + self.mypath + '/etc/enigma2 /etc/')
        elif cur == 'Satellites Terrestrial':
            self.mytext += _('Restore ') + cur + '\t\t\t' + ' [ OK ]\n'
            ret = system('cp -rf ' + self.mypath + '/etc/tuxbox /etc/')
        elif cur == 'Epg channels':
            self.mytext += _('Restore ') + cur + '\t\t\t' + ' [ OK ]\n'
            system('cp -rf ' + self.mypath + '/usr/share/dict /usr/share/')
        elif cur == 'Cams':
            self.mytext += _('Restore ') + cur + '\t\t\t\t' + ' [ OK ]\n'
            ret = system('cp -rf ' + self.mypath + '/usr/camscript /usr/')
            ret = system('cp -rf ' + self.mypath + '/usr/keys /usr/')
            ret = system('cp -rf ' + self.mypath + '/usr/scce /usr/')
            ret = system('cp -rf ' + self.mypath + '/etc/tuxbox/config /etc/tuxbox/')
        elif cur == 'Scripts':
            self.mytext += _('Restore ') + cur + '\t\t\t\t' + ' [ OK ]\n'
            ret = system('cp -rf ' + self.mypath + '/usr/script /usr/')
        elif cur == 'Bootlogo':
            self.mytext += _('Restore ') + cur + '\t\t\t' + ' [ OK ]\n'
            ret = system('cp -f ' + self.mypath + '/usr/share/*.mvi /usr/share/')
        elif cur == 'Plugins Extensions':
            self.mytext += _('Merge ') + cur + '\t\t\t' + ' [ OK ]\n'
            ret = self.mergepluginS('Extensions')
        elif cur == 'System Plugins':
            self.mytext += _('Merge ') + cur + '\t\t\t' + ' [ OK ]\n'
            ret = self.mergepluginS('SystemPlugins')
        if cur != 'END':
            self.count += 1
            self.activityTimer.start(100)
        else:
            self.mytext += '\nRestore Complete. Click OK to restart the box\n'
            self['lab1'].setText(self.mytext)
            ret = system('umount /media/bhbackuptmp')
            ret = system('rmdir /media/bhbackuptmp')
            ret = system('rm -rf ' + self.mypath)
            self.go = True

    def mergediR(self, path):
        opath = self.mypath + path
        destpath = path
        if isdir(opath) == True:
            if isdir(destpath) == True:
                odir = listdir(opath)
                destdir = listdir(destpath)
                for fil in odir:
                    if fil not in destdir:
                        f = opath + '/' + fil
                        system('cp -fd ' + f + ' ' + path + '/')

        return 0

    def mergepluginS(self, pdir):
        opath = self.mypath + '/usr/lib/enigma2/python/Plugins/' + pdir
        destpath = '/usr/lib/enigma2/python/Plugins/' + pdir
        odir = listdir(opath)
        destdir = listdir(destpath)
        for fil in odir:
            if fil not in destdir:
                f = opath + '/' + fil
                system('cp -rf ' + f + ' ' + destpath + '/')

        return 0

    def hrestBox(self):
        if self.go == True:
            system('reboot')


class Bh_Bpersonal_setuP(Screen, ConfigListScreen):
    skin = '\n\t<screen position="center,center" size="902,340" title="Black Hole Personal Backup Setup">\n\t\t<widget name="config" position="30,10" size="840,290" scrollbarMode="showOnDemand"/>\n\t\t<ePixmap pixmap="skin_default/buttons/red.png" position="200,300" size="140,40" alphatest="on"/>\n\t\t<ePixmap pixmap="skin_default/buttons/green.png" position="550,300" size="140,40" alphatest="on"/>\n\t\t<widget name="key_red" position="200,300" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1"/>\n\t\t<widget name="key_green" position="550,300" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1"/>\n\t</screen>'

    def __init__(self, session):
        Screen.__init__(self, session)
        self.list = []
        ConfigListScreen.__init__(self, self.list)
        self['key_red'] = Label(_('Save'))
        self['key_green'] = Label(_('Cancel'))
        self['actions'] = ActionMap(['WizardActions', 'ColorActions'], {'red': self.saveMysets,
         'green': self.close,
         'back': self.close})
        self.updateList()

    def updateList(self):
        mycf = myusb = mysd = myhdd = ''
        myoptions = []
        if fileExists('/proc/mounts'):
            f = open('/proc/mounts', 'r')
            for line in f.readlines():
                if line.find('/media/cf') != -1:
                    mycf = '/media/cf/'
                elif line.find('/media/usb') != -1:
                    myusb = '/media/usb/'
                elif line.find('/media/card') != -1:
                    mysd = '/media/card/'
                elif line.find('/hdd') != -1:
                    myhdd = '/media/hdd/'

            f.close()
        if mycf:
            myoptions.append((mycf, mycf))
        if myusb:
            myoptions.append((myusb, myusb))
        if mysd:
            myoptions.append((mysd, mysd))
        if myhdd:
            myoptions.append((myhdd, myhdd))
        self.list = []
        self.myepg_path = NoSave(ConfigSelection(choices=myoptions))
        if fileExists('/etc/bhpersonalbackup'):
            f = open('/etc/bhpersonalbackup', 'r')
            self.myepg_path.value = f.readline().strip()
            f.close()
        epg_path = getConfigListEntry(_('Path to save Personal Backup'), self.myepg_path)
        self.list.append(epg_path)
        self['config'].list = self.list
        self['config'].l.setList(self.list)

    def saveMysets(self):
        out = open('/etc/bhpersonalbackup', 'w')
        out.write(self.myepg_path.value)
        out.close()
        self.close()


class Bh_Bpersonal_baK(Screen):
    skin = '\n\t<screen position="center,center" size="600,300" title="Black Hole Backup in progress..." flags="wfNoBorder">\n\t\t<widget name="connect" position="0,0" size="600,300" zPosition="-1" pixmaps="/usr/lib/enigma2/python/Plugins/Extensions/BhPersonalBackup/icons/backup_1.png,/usr/lib/enigma2/python/Plugins/Extensions/BhPersonalBackup/icons/backup_2.png,/usr/lib/enigma2/python/Plugins/Extensions/BhPersonalBackup/icons/backup_3.png,/usr/lib/enigma2/python/Plugins/Extensions/BhPersonalBackup/icons/backup_4.png,/usr/lib/enigma2/python/Plugins/Extensions/BhPersonalBackup/icons/backup_5.png,/usr/lib/enigma2/python/Plugins/Extensions/BhPersonalBackup/icons/backup_6.png"  />\n\t\t<widget name="lab1" position="0,240" halign="center" size="600,60" zPosition="1" font="Regular;20" valign="top" transparent="1" />\n\t</screen>'

    def __init__(self, session):
        Screen.__init__(self, session)
        self['connect'] = MultiPixmap()
        self['connect'].setPixmapNum(0)
        self['lab1'] = Label('')
        self.mylist = ['Libraries',
         'Binaries',
         'Cams',
         'Scripts',
         'Bootlogos',
         'Uninstall files',
         'General Settings',
         'Cron',
         'Settings Channels Bouquets',
         'Openvpn',
         'Satellites Terrestrial',
         'Plugins',
         'END']
        self.mytmppath = '/media/hdd/'
        if fileExists('/etc/bhpersonalbackup'):
            f = open('/etc/bhpersonalbackup', 'r')
            self.mytmppath = f.readline().strip()
            f.close()
        self.mytmppath += 'bhbackuptmp'
        self.activityTimer = eTimer()
        self.activityTimer.timeout.get().append(self.updatepix)
        self.onShow.append(self.startShow)
        self.onClose.append(self.delTimer)
        system('rm -rf ' + self.mytmppath)
        system('mkdir ' + self.mytmppath)
        system('mkdir ' + self.mytmppath + '/etc')
        system('mkdir ' + self.mytmppath + '/usr')
        configfile.save()

    def startShow(self):
        self.curpix = 0
        self.count = 0
        self.procesS()

    def updatepix(self):
        self.activityTimer.stop()
        self['connect'].setPixmapNum(self.curpix)
        self.curpix += 1
        if self.curpix == 6:
            self.curpix = 0
            self.procesS()
        else:
            self.activityTimer.start(150)

    def procesS(self):
        cur = self.mylist[self.count]
        self['lab1'].setText(cur)
        if cur == 'Libraries':
            ret = system('mkdir ' + self.mytmppath + '/usr/lib')
            ret = system('cp -fd /usr/lib/* ' + self.mytmppath + '/usr/lib')
        elif cur == 'Binaries':
            ret = system('cp -fdr /usr/bin ' + self.mytmppath + '/usr')
        elif cur == 'Cams':
            ret = system('cp -rf /usr/camscript ' + self.mytmppath + '/usr')
            ret = system('cp -rf /usr/keys ' + self.mytmppath + '/usr')
            ret = system('cp -rf /usr/scce ' + self.mytmppath + '/usr')
            ret = system('cp -rf /usr/scam ' + self.mytmppath + '/usr')
        elif cur == 'Scripts':
            ret = system('cp -rf /usr/script ' + self.mytmppath + '/usr')
        elif cur == 'Bootlogos':
            ret = system('mkdir ' + self.mytmppath + '/usr/share')
            ret = system('cp -f /usr/share/*.mvi ' + self.mytmppath + '/usr/share')
        elif cur == 'Uninstall files':
            ret = system('cp -rf /usr/uninstall ' + self.mytmppath + '/usr')
        elif cur == 'General Settings':
            ret = system('mkdir ' + self.mytmppath + '/etc/rc3.d')
            ret = system('cp -fd /etc/rc3.d/* ' + self.mytmppath + '/etc/rc3.d/')
            ret = system('mkdir ' + self.mytmppath + '/etc/network')
            ret = system('cp -f /etc/* ' + self.mytmppath + '/etc')
            ret = system('cp -f /etc/network/interfaces ' + self.mytmppath + '/etc/network')
        elif cur == 'Cron':
            ret = system('cp -rf /etc/bhcron ' + self.mytmppath + '/etc')
        elif cur == 'Settings Channels Bouquets':
            ret = system('mkdir ' + self.mytmppath + '/usr/share/enigma2')
            ret = system('cp -rf /etc/enigma2 ' + self.mytmppath + '/etc')
            ret = system('cp -rf /usr/share/dict ' + self.mytmppath + '/usr/share')
            ret = system('cp -f /usr/share/enigma2/keymap.xml ' + self.mytmppath + '/usr/share/enigma2/')
        elif cur == 'Openvpn':
            ret = system('cp -rf /etc/openvpn ' + self.mytmppath + '/etc')
        elif cur == 'Satellites Terrestrial':
            ret = system('cp -rf /etc/tuxbox ' + self.mytmppath + '/etc')
        elif cur == 'Plugins':
            ret = system('mkdir ' + self.mytmppath + '/usr/lib/enigma2')
            ret = system('mkdir ' + self.mytmppath + '/usr/lib/enigma2/python')
            ret = system('mkdir ' + self.mytmppath + '/usr/lib/enigma2/python/Plugins')
            ret = system('cp -rf /usr/lib/enigma2/python/Plugins/Extensions ' + self.mytmppath + '/usr/lib/enigma2/python/Plugins')
            ret = system('cp -rf /usr/lib/enigma2/python/Plugins/SystemPlugins ' + self.mytmppath + '/usr/lib/enigma2/python/Plugins')
            self['lab1'].setText('Plugins')
        if cur != 'END':
            self.count += 1
            self.activityTimer.start(100)
        else:
            mydir = getcwd()
            chdir(self.mytmppath)
            cmd = 'tar -cf BhPersonalBackup.tar etc usr'
            rc = system(cmd)
            os_rename('BhPersonalBackup.tar', '../BhPersonalBackup.bh5')
            chdir(mydir)
            self.session.open(MessageBox, _('Backup complete !'), MessageBox.TYPE_INFO)
            self.close()

    def delTimer(self):
        del self.activityTimer
        system('rm -rf ' + self.mytmppath)


def main(session, **kwargs):
    session.open(Bh_Bpersonal_main)


def menu(menuid, **kwargs):
    if menuid == 'bhbackup':
        return [(_('BlackHole Personal Backup'),
          main,
          'BlackHolePersonalBackup',
          2)]
    return []


def Plugins(**kwargs):
    return PluginDescriptor(name='BlackHolePersonalBackup', description=_('Black Hole personal backup'), where=PluginDescriptor.WHERE_MENU, fnc=menu)
