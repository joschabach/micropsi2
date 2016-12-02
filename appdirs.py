#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=C0103
# Copyright (c) 2005-2010 ActiveState Software Inc.
# Copyright (c) 2013 Eddy Petrișor

"""Utilities for determining application-specific dirs.

See <http://github.com/Kriskras99/appdirs> for details and usage.
"""
# Dev Notes:
# - MSDN on where to store app data files:
#   http://support.microsoft.com/default.aspx?scid=kb;en-us;310294#XSLTH3194121123120121120120
#   https://msdn.microsoft.com/en-us/library/windows/desktop/dd378457(v=vs.85).aspx
# - Mac OS X: 
#   https://developer.apple.com/library/content/documentation/FileManagement/Conceptual/FileSystemProgrammingGuide/FileSystemOverview/FileSystemOverview.html
# - XDG spec for Un*x: http://standards.freedesktop.org/basedir-spec/basedir-spec-latest.html

__version_info__ = (1, 4, 1)
__version__ = '.'.join(map(str, __version_info__))


import sys
import os

PY3 = sys.version_info[0] == 3

if PY3:
    unicode = str

if sys.platform.startswith('java'):
    import platform
    os_name = platform.java_ver()[3][0]
    if os_name.startswith('Windows'): # "Windows XP", "Windows 7", etc.
        system = 'win32'
    elif os_name.startswith('Mac'): # "Mac OS X", etc.
        system = 'darwin'
    else: # "Linux", "SunOS", "FreeBSD", etc.
        # Setting this to "linux2" is not ideal, but only Windows or Mac
        # are actually checked for and the rest of the module expects
        # *sys.platform* style strings.
        system = 'linux2'
else:
    system = sys.platform



def user_data_dir(appname=None, appauthor=None, version=None, roaming=False):
    r"""Return full path to the user-specific data dir for this application.

        "appname" is the name of application.
            If None, just the system directory is returned.
        "appauthor" (only used on Windows) is the name of the
            appauthor or distributing body for this application. Typically
            it is the owning company name. This falls back to appname. You may
            pass False to disable it.
        "version" is an optional version path element to append to the
            path. You might want to use this if you want multiple versions
            of your app to be able to run independently. If used, this
            would typically be "<major>.<minor>".
            Only applied when appname is present.
        "roaming" (boolean, default False) can be set True to use the Windows
            roaming appdata directory. That means that for users on a Windows
            network setup for roaming profiles, this user data will be
            sync'd on login. See
            <http://technet.microsoft.com/en-us/library/cc766489(WS.10).aspx>
            for a discussion of issues.

    Typical user data directories are:
        Mac OS X:               ~/Library/Application Support/<AppAuthor>/<AppName>
        Unix:                   ~/.local/share/<AppName>    # or in $XDG_DATA_HOME, if defined
        Win 7  (not roaming):   C:\Users\<username>\AppData\Local\<AppAuthor>\<AppName>
        Win 7  (roaming):       C:\Users\<username>\AppData\Roaming\<AppAuthor>\<AppName>

    For Unix, we follow the XDG spec and support $XDG_DATA_HOME.
    That means, by default "~/.local/share/<AppName>".
    """
    if system == "win32":
        if appauthor is None:
            appauthor = appname
        if roaming:
            path = os.getenv('APPDATA', _get_win_folder_from_knownid('{3EB685DB-65F9-4CF6-A03A-E3EF65729F3D}'))
        else:
            path = os.getenv('LOCALAPPDATA', _get_win_folder_from_knownid('{F1B32785-6FBA-4FCF-9D55-7B8E7F157091}'))
        if appname:
            if appauthor:
                path = os.path.join(path, appauthor, appname)
            else:
                path = os.path.join(path, appname)
    elif system == 'darwin':
        path = os.path.expanduser('~/Library/Application Support/')
        if appname:
            if appauthor:
                path = os.path.join(path, appauthor, appname)
            else:
                path = os.path.join(path, appname)
    else:
        path = os.getenv('XDG_DATA_HOME', os.path.expanduser("~/.local/share"))
        if appname:
            path = os.path.join(path, appname)
    if appname and version:
        path = os.path.join(path, str(version))
    return path

def site_data_dir(appname=None, appauthor=None, version=None, multipath=False):
    r"""Return full path to the user-shared data dir for this application.

        "appname" is the name of application.
            If None, just the system directory is returned.
        "appauthor" (only used on Windows) is the name of the
            appauthor or distributing body for this application. Typically
            it is the owning company name. This falls back to appname. You may
            pass False to disable it.
        "version" is an optional version path element to append to the
            path. You might want to use this if you want multiple versions
            of your app to be able to run independently. If used, this
            would typically be "<major>.<minor>".
            Only applied when appname is present.
        "multipath" is an optional parameter only applicable to *nix
            which indicates that the entire list of data dirs should be
            returned. By default, the first item from XDG_DATA_DIRS is
            returned, or '/usr/local/share/<AppName>',
            if XDG_DATA_DIRS is not set

    Typical site data directories are:
        Mac OS X:   /Library/Application Support/<AppAuthor>/<AppName>
        Unix:       /usr/local/share/<AppName> or /usr/share/<AppName>
        Vista:      (Fail! "C:\ProgramData" is a hidden *system* directory on Vista.)
        Win 7:      C:\ProgramData\<AppAuthor>\<AppName>   # Hidden, but writeable on Win 7.

    For Unix, this is using the $XDG_DATA_DIRS[0] default.

    WARNING: Do not use this on Windows. See the Vista-Fail note above for why.
    """
    if system == "win32":
        if appauthor is None:
            appauthor = appname
        path = os.getenv('ALLUSERSPROFILE', _get_win_folder_from_knownid('{62AB5D82-FDC1-4DC3-A9DD-070D1D495D97}'))
        if appname:
            if appauthor:
                path = os.path.join(path, appauthor, appname)
            else:
                path = os.path.join(path, appname)
    elif system == 'darwin':
        path = os.path.expanduser('/Library/Application Support')
        if appname:
            if appauthor:
                path = os.path.join(path, appauthor, appname)
            else:
                path = os.path.join(path, appname)
    else:
        # XDG default for $XDG_DATA_DIRS
        # only first, if multipath is False
        path = os.getenv('XDG_DATA_DIRS',
                         os.pathsep.join(['/usr/local/share', '/usr/share']))
        pathlist = [os.path.expanduser(x.rstrip(os.sep)) for x in path.split(os.pathsep)]
        if appname:
            if version:
                appname = os.path.join(appname, str(version))
            pathlist = [os.sep.join([x, appname]) for x in pathlist]

        if multipath:
            path = os.pathsep.join(pathlist)
        else:
            path = pathlist[0]
        return path

    if appname and version:
        path = os.path.join(path, str(version))
    return path


def user_config_dir(appname=None, appauthor=None, version=None, roaming=False):
    r"""Return full path to the user-specific config dir for this application.

        "appname" is the name of application.
            If None, just the system directory is returned.
        "appauthor" (only used on Windows) is the name of the
            appauthor or distributing body for this application. Typically
            it is the owning company name. This falls back to appname. You may
            pass False to disable it.
        "version" is an optional version path element to append to the
            path. You might want to use this if you want multiple versions
            of your app to be able to run independently. If used, this
            would typically be "<major>.<minor>".
            Only applied when appname is present.
        "roaming" (boolean, default False) can be set True to use the Windows
            roaming appdata directory. That means that for users on a Windows
            network setup for roaming profiles, this user data will be
            sync'd on login. See
            <http://technet.microsoft.com/en-us/library/cc766489(WS.10).aspx>
            for a discussion of issues.

    Typical site data directories are:
        Mac OS X:               ~/Library/Preferences/<AppAuthor>/<AppName>
        Unix:                   ~/.config/<AppName>     # or in $XDG_CONFIG_HOME, if defined
        Win *:                  same as user_data_dir

    For Unix, we follow the XDG spec and support $XDG_CONFIG_HOME.
    That means, by default "~/.config/<AppName>".
    """
    if system == "win32":
        path = user_data_dir(appname, appauthor, None, roaming)
    elif system == 'darwin':
        path = os.path.expanduser('~/Library/Preferences/')
        if appname:
            if appauthor:
                path = os.path.join(path, appauthor, appname)
            else:
                path = os.path.join(path, appname)
    else:
        path = os.getenv('XDG_CONFIG_HOME', os.path.expanduser("~/.config"))
        if appname:
            path = os.path.join(path, appname)
    if appname and version:
        path = os.path.join(path, str(version))
    return path


def site_config_dir(appname=None, appauthor=None, version=None, multipath=False):
    r"""Return full path to the user-shared data dir for this application.

        "appname" is the name of application.
            If None, just the system directory is returned.
        "appauthor" (only used on Windows) is the name of the
            appauthor or distributing body for this application. Typically
            it is the owning company name. This falls back to appname. You may
            pass False to disable it.
        "version" is an optional version path element to append to the
            path. You might want to use this if you want multiple versions
            of your app to be able to run independently. If used, this
            would typically be "<major>.<minor>".
            Only applied when appname is present.
        "multipath" is an optional parameter only applicable to *nix
            which indicates that the entire list of config dirs should be
            returned. By default, the first item from XDG_CONFIG_DIRS is
            returned, or '/etc/xdg/<AppName>', if XDG_CONFIG_DIRS is not set

    Typical site data directories are:
        Mac OS X:   /Library/Preferences/<AppAuthor>/<AppName>
        Unix:       /etc/xdg/<AppName> or $XDG_CONFIG_DIRS[i]/<AppName> for each value in
                    $XDG_CONFIG_DIRS
        Win *:      same as site_data_dir
        Vista:      (Fail! "C:\ProgramData" is a hidden *system* directory on Vista.)

    For Unix, this is using the $XDG_CONFIG_DIRS[0] default, if multipath=False

    WARNING: Do not use this on Windows. See the Vista-Fail note above for why.
    """
    if system == 'win32':
        path = site_data_dir(appname, appauthor)
        if appname and version:
            path = os.path.join(path, str(version))
    elif system == 'darwin':
        path = os.path.expanduser('/Library/Preferences')
        if appname:
            if appauthor:
                path = os.path.join(path, appauthor, appname)
            else:
                path = os.path.join(path, appname)
            if version:
                path = os.path.join(path, str(version))
    else:
        # XDG default for $XDG_CONFIG_DIRS
        # only first, if multipath is False
        path = os.getenv('XDG_CONFIG_DIRS', '/etc/xdg')
        pathlist = [os.path.expanduser(x.rstrip(os.sep)) for x in path.split(os.pathsep)]
        if appname:
            if version:
                appname = os.path.join(appname, str(version))
            pathlist = [os.sep.join([x, appname]) for x in pathlist]

        if multipath:
            path = os.pathsep.join(pathlist)
        else:
            path = pathlist[0]
    return path


def user_cache_dir(appname=None, appauthor=None, version=None, opinion=True):
    r"""Return full path to the user-specific cache dir for this application.

        "appname" is the name of application.
            If None, just the system directory is returned.
        "appauthor" (only used on Windows) is the name of the
            appauthor or distributing body for this application. Typically
            it is the owning company name. This falls back to appname. You may
            pass False to disable it.
        "version" is an optional version path element to append to the
            path. You might want to use this if you want multiple versions
            of your app to be able to run independently. If used, this
            would typically be "<major>.<minor>".
            Only applied when appname is present.
        "opinion" (boolean) can be False to disable the appending of
            "Cache" to the base app data dir for Windows. See
            discussion below.

    Typical user cache directories are:
        Mac OS X:   ~/Library/Caches/<AppAuthor>/<AppName>
        Unix:       ~/.cache/<AppName> (XDG default)
        Vista:      C:\Users\<username>\AppData\Local\<AppAuthor>\<AppName>\Cache

    On Windows the only suggestion in the MSDN docs is that local settings go in
    the `CSIDL_LOCAL_APPDATA` directory. This is identical to the non-roaming
    app data dir (the default returned by `user_data_dir` above). Apps typically
    put cache data somewhere *under* the given dir here. Some examples:
        ...\Mozilla\Firefox\Profiles\<ProfileName>\Cache
        ...\Acme\SuperApp\Cache\1.0
    OPINION: This function appends "Cache" to the `CSIDL_LOCAL_APPDATA` value.
    This can be disabled with the `opinion=False` option.
    """
    if system == "win32":
        if appauthor is None:
            appauthor = appname
        path = os.getenv('LOCALAPPDATA', _get_win_folder_from_knownid('{F1B32785-6FBA-4FCF-9D55-7B8E7F157091}'))
        if appname:
            if appauthor:
                path = os.path.join(path, appauthor, appname)
            else:
                path = os.path.join(path, appname)
            if opinion:
                path = os.path.join(path, "Cache")
    elif system == 'darwin':
        path = os.path.expanduser('~/Library/Caches')
        if appname:
            if appauthor:
                path = os.path.join(path, appauthor, appname)
            else:
                path = os.path.join(path, appname)
    else:
        path = os.getenv('XDG_CACHE_HOME', os.path.expanduser('~/.cache'))
        if appname:
            path = os.path.join(path, appname)
    if appname and version:
        path = os.path.join(path, str(version))
    return path

def user_state_dir(appname=None, appauthor=None, version=None):
    r"""Return full path to the user-specific state dir for this application.
        "appname" is the name of application.
            If None, just the system directory is returned.
        "appauthor" (only used on Windows) is the name of the
            appauthor or distributing body for this application. Typically
            it is the owning company name. This falls back to appname. You may
            pass False to disable it.
        "version" is an optional version path element to append to the
            path. You might want to use this if you want multiple versions
            of your app to be able to run independently. If used, this
            would typically be "<major>.<minor>".
            Only applied when appname is present.
    Typical user state directories are:
        Mac OS X:  same as user_data_dir
        Unix:      ~/.local/state/<AppName>   # or in $XDG_STATE_HOME, if defined
        Win *:     same as user_data_dir
    For Unix, we follow this Debian proposal <https://wiki.debian.org/XDGBaseDirectorySpecification#state>
    to extend the XDG spec and support $XDG_STATE_HOME.
    That means, by default "~/.local/state/<AppName>".
    """
    if system in ["win32", "darwin"]:
        path = user_data_dir(appname, appauthor, version=None, roaming=False)
    else:
        path = os.getenv('XDG_STATE_HOME', os.path.expanduser("~/.local/state"))
        if appname:
            path = os.path.join(path, appname)
    if appname and version:
        path = os.path.join(path, str(version))
    return path

def user_log_dir(appname=None, appauthor=None, version=None, opinion=True):
    r"""Return full path to the user-specific log dir for this application.

        "appname" is the name of application.
            If None, just the system directory is returned.
        "appauthor" (only used on Windows) is the name of the
            appauthor or distributing body for this application. Typically
            it is the owning company name. This falls back to appname. You may
            pass False to disable it.
        "version" is an optional version path element to append to the
            path. You might want to use this if you want multiple versions
            of your app to be able to run independently. If used, this
            would typically be "<major>.<minor>".
            Only applied when appname is present.
        "opinion" (boolean) can be False to disable the appending of
            "Logs" to the base app data dir for Windows, and "log" to the
            base cache dir for Unix. See discussion below.

    Typical user log directories are:
        Mac OS X:   ~/Library/Logs/<AppAuthor>/<AppName>
        Unix:       ~/.cache/<AppName>/log  # or under $XDG_CACHE_HOME if defined
        Vista:      C:\Users\<username>\AppData\Local\<AppAuthor>\<AppName>\Logs

    On Windows the only suggestion in the MSDN docs is that local settings
    go in the `CSIDL_LOCAL_APPDATA` directory. (Note: I'm interested in
    examples of what some windows apps use for a logs dir.)

    OPINION: This function appends "Logs" to the `CSIDL_LOCAL_APPDATA`
    value for Windows and appends "log" to the user cache dir for Unix.
    This can be disabled with the `opinion=False` option.
    """
    if system == "darwin":
        path = os.path.expanduser('~/Library/Logs')
        if appname:
            if appauthor:
                path = os.path.join(path, appauthor, appname)
            else:
                path = os.path.join(path, appname)
    elif system == "win32":
        path = user_data_dir(appname, appauthor, str(version))
        version = False
        if opinion:
            path = os.path.join(path, "Logs")
    else:
        path = user_cache_dir(appname, appauthor, str(version))
        version = False
        if opinion:
            path = os.path.join(path, "log")
    if appname and version:
        path = os.path.join(path, str(version))
    return path

def user_desktop_dir():
    r"""Return full path to the user's desktop directory.

    Typical user desktop directories are:
        Mac OS X:   ~/Desktop
        Unix:       ~/Desktop  # or under $XDG_DESKTOP_DIR if defined
        Windows:    C:\Users\<username>\Desktop

    Returns
    -------
    path : str
        Returns a full path to the directory.
    """
    if system == "darwin":
        path = os.path.expanduser('~/Desktop')
    elif system == "win32":
        path = _get_win_folder_from_knownid('{B4BFCC3A-DB2C-424C-B029-7FE99A87C641}')
    else:
        path = os.getenv('XDG_DESKTOP_DIR', xdg_user_dirs['XDG_DESKTOP_DIR'])
    return path

def user_documents_dir(appname=None, appauthor=None, version=None):
    r"""Return full path to the user's documents directory.

    Typical user documents directories are:
        Mac OS X:   ~/Documents
        Unix:       ~/Documents  # or under $XDG_DOCUMENTS_DIR if defined
        Windows:    C:\Users\<username>\Documents

    Params
    ------
    appname : str, optional
        The name of the application, if None just the documents directory
        is returned.
    appauthor : str, optional
        The name of the appauthor or distributing body. Not used on Linux.
    version : str, optional
        The version of the application.
    Returns
    -------
    path : str
        Returns a full path to the directory.
    """
    if system == "darwin":
        path = os.path.expanduser('~/Documents')
    elif system == "win32":
        path = _get_win_folder_from_knownid('{FDD39AD0-238F-46AF-ADB4-6C85480369C7}')
    else:
        path = os.getenv('XDG_DOCUMENTS_DIR', xdg_user_dirs['XDG_DOCUMENTS_DIR'])
    return path

def user_download_dir():
    r"""Return full path to the user's downloads directory.

    Typical user desktop directories are:
        Mac OS X:   ~/Downloads
        Unix:       ~/Downloads  # or under $XDG_DOWNLOAD_DIR if defined
        Windows:    C:\Users\<username>\Downloads

    Returns
    -------
    path : str
        Returns a full path to the directory.
    """
    if system == "darwin":
        path = os.path.expanduser('~/Downloads')
    elif system == "win32":
        path = _get_win_folder_from_knownid('{374DE290-123F-4565-9164-39C4925E467B}')
    else:
        path = os.getenv('XDG_DOWNLOAD_DIR', xdg_user_dirs['XDG_DOWNLOAD_DIR'])
    return path

def user_music_dir():
    r"""Return full path to the user's music directory.

    Typical user desktop directories are:
        Mac OS X:   ~/Music
        Unix:       ~/Music  # or under $XDG_MUSIC_DIR if defined
        Windows:    C:\Users\<username>\Music

    Returns
    -------
    path : str
        Returns a full path to the directory.
    """
    if system == "darwin":
        path = os.path.expanduser('~/Music')
    elif system == "win32":
        path = _get_win_folder_from_knownid('{4BD8D571-6D19-48D3-BE97-422220080E43}')
    else:
        path = os.getenv('XDG_MUSIC_DIR', xdg_user_dirs['XDG_MUSIC_DIR'])
    return path

def user_pictures_dir():
    r"""Return full path to the user's pictures directory.

    Typical user desktop directories are:
        Mac OS X:   ~/Pictures
        Unix:       ~/Pictures  # or under $XDG_PICTURES_DIR if defined
        Windows:    C:\Users\<username>\Pictures

    Returns
    -------
    path : str
        Returns a full path to the directory.
    """
    if system == "darwin":
        path = os.path.expanduser('~/Pictures')
    elif system == "win32":
        path = _get_win_folder_from_knownid('{33E28130-4E1E-4676-835A-98395C3BC3BB}')
    else:
        path = os.getenv('XDG_PICTURES_DIR', xdg_user_dirs['XDG_PICTURES_DIR'])
    return path

def user_publicshare_dir():
    r"""Return full path to the user's public directory.

    Typical user desktop directories are:
        Mac OS X:   ~/Public
        Unix:       ~/Public  # or under $XDG_PUBLICSHARE_DIR if defined
        Windows:    C:\Users\Public

    .. note:: Not the same sort directory on Linux/OS X and Windows,
              On Windows it's a seperate user, on OSX/Linux it's a
              directory in the home folder.

    Returns
    -------
    path : str
        Returns a full path to the directory.
    """
    if system == "darwin":
        path = os.path.expanduser('~/Public')
    elif system == "win32":
        path = _get_win_folder_from_knownid('{DFDF76A2-C82A-4D63-906A-5644AC457385}')
    else:
        path = os.getenv('XDG_PUBLICSHARE_DIR', xdg_user_dirs['XDG_PUBLICSHARE_DIR'])
    return path

def user_templates_dir(appname=None, appauthor=None, version=None):
    r"""Return full path to the user's template directory.

    Typical user desktop directories are:
        Mac OS X:   ~/Desktop
        Unix:       ~/Templates  # or under $XDG_TEMPLATE_DIR if defined
        Windows:    C:\Users\<username>\Desktop

    .. note:: Not the same sort directory on Windows/Linux and OS X,
              On Mac OS X these templates can only be used by the application that
              created them. On Windows/Linux they are added to the context menu.

    Params
    ------
    appname : str, optional
        The name of the application. If None, just the system directory
        is returned. Only used on Mac OS X.
    appauthor : str, optional
        The name of the appauthor or distributing body for this application. Typically
        it is the owning company name.
    version : str or int, optional
        An optional version path element to append to the path. You might
        want to use this if you want multiple versions of your app to be able
        to run independently. If used, this would typically be "<mayor>.<minor>".
        Only used on Mac OS X.

    Returns
    -------
    path : str
        Returns a full path to the directory.

    Notes
    -----
    The Mac OS X implementation is based on Microsoft Office' template directory [2]_

    References
    ----------
    .. [2] https://support.office.com/en-us/article/Create-and-use-your-own-template-a1b72758-61a0-4215-80eb-165c6c4bed04
    """
    if system == "darwin":
        path = os.path.join(user_data_dir(appname=appname, appauthor=appauthor, version=version), 'User Templates')
    elif system == "win32":
        path = _get_win_folder_from_knownid('{A63293E8-664E-48DB-A079-DF759E0509F7}')
    else:
        path = os.getenv('XDG_TEMPLATES_DIR', xdg_user_dirs['XDG_TEMPLATES_DIR'])
    return path

def user_videos_dir():
    r"""Return full path to the user's videos directory.

    Typical user desktop directories are:
        Mac OS X:   ~/Desktop
        Unix:       ~/Desktop  # or under $XDG_DESKTOP_DIR if defined
        Windows:    C:\Users\<username>\Desktop

    Returns
    -------
    path : str
        Returns a full path to the directory.
    """
    if system == "darwin":
        path = os.path.expanduser('~/Videos')
    elif system == "win32":
        path = _get_win_folder_from_knownid('{18989B1D-99B5-455B-841C-AB7C74E4DDFC}')
    else:
        path = os.getenv('XDG_VIDEOS_DIR', xdg_user_dirs['XDG_VIDEOS_DIR'])
    return path


class AppDirs(object):
    """Convenience wrapper for getting application dirs."""
    def __init__(self, appname=None, appauthor=None, version=None,
                 roaming=False, multipath=False):
        self.appname = appname
        self.appauthor = appauthor
        self.version = version
        self.roaming = roaming
        self.multipath = multipath

    @property
    def user_data_dir(self):
        """Return full path to the user-specific data dir for this application."""
        return user_data_dir(self.appname, self.appauthor,
                             version=self.version, roaming=self.roaming)

    @property
    def site_data_dir(self):
        """Return full path to the user-shared data dir for this application."""
        return site_data_dir(self.appname, self.appauthor,
                             version=self.version, multipath=self.multipath)

    @property
    def user_config_dir(self):
        """Return full path to the user-specific config dir for this application."""
        return user_config_dir(self.appname, self.appauthor,
                               version=self.version, roaming=self.roaming)

    @property
    def site_config_dir(self):
        """Return full path to the user-shared data dir for this application."""
        return site_config_dir(self.appname, self.appauthor,
                               version=self.version, multipath=self.multipath)

    @property
    def user_cache_dir(self):
        """Return full path to the user-specific cache dir for this application."""
        return user_cache_dir(self.appname, self.appauthor,
                              version=self.version)

    @property
    def user_state_dir(self):
        """Return full path to the user-specific state dir for this application."""
        return user_state_dir(self.appname, self.appauthor,
                              version=self.version)

    @property
    def user_log_dir(self):
        """Return full path to the user-specific log dir for this application."""
        return user_log_dir(self.appname, self.appauthor,
                            version=self.version)

    @property
    def user_desktop_dir(self):
        """Return full path to the user's desktop dir."""
        return user_desktop_dir()

    @property
    def user_documents_dir(self):
        """Return full path to the user's documents dir."""
        return user_documents_dir()

    @property
    def user_download_dir(self):
        """Return full path to the user's download dir."""
        return user_download_dir()

    @property
    def user_music_dir(self):
        """Return full path to the user's music dir."""
        return user_music_dir()

    @property
    def user_pictures_dir(self):
        """Return full path to the user's pictures dir."""
        return user_pictures_dir()

    @property
    def user_publicshare_dir(self):
        """Return full path to the user's public dir."""
        return user_publicshare_dir()

    @property
    def user_templates_dir(self):
        """Return full path to the user's templates dir."""
        return user_templates_dir(self.appname, self.appauthor, self.version)

    @property
    def user_videos_dir(self):
        """Return full path to the user's videos dir."""
        return user_videos_dir()

#---- Internal support stuff
def _get_win_folder_from_knownid(folderid, userhandle=0):
    """Get folder path from KNOWNFOLDERID.

    Based of code by mkropat [https://gist.github.com/mkropat/7550097] licensed under MIT.

    Params
    ------
    userhandle:
        0 for current user, -1 for common/shared folder
    folderid:
        A GUID listed at [https://msdn.microsoft.com/en-us/library/windows/desktop/dd378457.aspx]
    """
    import ctypes
    from ctypes import windll, wintypes
    from uuid import UUID


    class GUID(ctypes.Structure):
        _fields_ = [
            ("Data1", wintypes.DWORD),
            ("Data2", wintypes.WORD),
            ("Data3", wintypes.WORD),
            ("Data4", wintypes.BYTE * 8)
        ] 

        def __init__(self, uuid_):
            ctypes.Structure.__init__(self)
            self.Data1, self.Data2, self.Data3, self.Data4[0], self.Data4[1], rest = uuid_.fields
            for i in range(2, 8):
                self.Data4[i] = rest>>(8 - i - 1)*8 & 0xff

    _CoTaskMemFree = windll.ole32.CoTaskMemFree
    _CoTaskMemFree.restype = None
    _CoTaskMemFree.argtypes = [ctypes.c_void_p]

    _SHGetKnownFolderPath = windll.shell32.SHGetKnownFolderPath
    _SHGetKnownFolderPath.argtypes = [
        ctypes.POINTER(GUID), wintypes.DWORD, wintypes.HANDLE, ctypes.POINTER(ctypes.c_wchar_p)
    ]

    fid = GUID(UUID(folderid))
    pPath = ctypes.c_wchar_p()
    if _SHGetKnownFolderPath(ctypes.byref(fid), 0, userhandle, ctypes.byref(pPath)) != 0:
        raise WindowsError("Path not found for folderid: %s and userhandle: %s" % (folderid, userhandle))
    path = pPath.value
    _CoTaskMemFree(pPath)
    return path

if system.startswith('linux'): # For reading from user-dirs.dirs file
    xdg_user_dirs = {
        "XDG_DESKTOP_DIR": os.path.expanduser("~/Desktop"),
        "XDG_DOCUMENTS_DIR": os.path.expanduser("~/Documents"),
        "XDG_DOWNLOAD_DIR": os.path.expanduser("~/Downloads"),
        "XDG_MUSIC_DIR": os.path.expanduser("~/Music"),
        "XDG_PICTURES_DIR": os.path.expanduser("~/Pictures"),
        "XDG_PUBLICSHARE_DIR": os.path.expanduser("~/Public"),
        "XDG_TEMPLATES_DIR": os.path.expanduser("~/Templates"),
        "XDG_VIDEOS_DIR": os.path.expanduser("~/Videos")
    }
    try:
        with open(os.path.join(user_config_dir(), 'user-dirs.dirs')) as f:
            for shvar in f.readlines():
                if shvar.startswith('#'): # Skip comments
                    continue
                shvar = shvar.rstrip() # Remove newlines
                key = shvar.split('=')[0]
                value = shvar.split('=')[1].strip("\"'")
                while '$' in value:
                    start = value.find('$')
                    a = value.find('/', start)
                    b = value.find('\\', start)
                    if a > b: end = a
                    if a < b: end = b
                    if a == b: end = len(value)
                    try:
                        value = value[:start] + os.environ[value[start+1:end]] + value[end:]
                    except KeyError:
                        continue
                xdg_user_dirs[key] = value
            f.close()
    except IOError:
        pass
