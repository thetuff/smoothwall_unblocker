import sys
from pathlib import Path

from PyQt6.QtCore import QUrl, Qt, QSize
from PyQt6.QtGui import QAction, QIcon, QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QToolBar,
    QLineEdit,
    QTabWidget,
    QWidget,
    QVBoxLayout,
    QTabBar,
)
from PyQt6.QtWebEngineCore import (
    QWebEnginePage,
    QWebEngineProfile,
    QWebEngineSettings,
)
from PyQt6.QtWebEngineWidgets import QWebEngineView


# ============================================================
# SETTINGS
# ============================================================

APP_NAME = "Nova Browser"

DATA_DIR = Path.home() / ".nova_browser"
DATA_DIR.mkdir(exist_ok=True)


# ============================================================
# BROWSER PAGE
# ============================================================

class BrowserPage(QWebEnginePage):

    def __init__(self, profile, browser_window):
        super().__init__(profile, browser_window)
        self.browser_window = browser_window

    def createWindow(self, window_type):
        """
        Websites that try to open a new window/tab
        are opened as a new browser tab instead.
        """

        if window_type in (
            QWebEnginePage.WebWindowType.WebBrowserWindow,
            QWebEnginePage.WebWindowType.WebBrowserTab,
            QWebEnginePage.WebWindowType.WebDialog,
        ):
            return self.browser_window.create_browser_page()

        return super().createWindow(window_type)


# ============================================================
# BROWSER TAB
# ============================================================

class BrowserTab(QWidget):

    def __init__(self, browser_window, url=None):
        super().__init__()

        self.browser_window = browser_window

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.webview = QWebEngineView()

        self.page = BrowserPage(
            self.browser_window.profile,
            self.browser_window
        )

        self.webview.setPage(self.page)

        # ----------------------------------------------------
        # WEB ENGINE SETTINGS
        # ----------------------------------------------------

        settings = self.webview.settings()

        settings.setAttribute(
            QWebEngineSettings.WebAttribute.JavascriptEnabled,
            True
        )

        settings.setAttribute(
            QWebEngineSettings.WebAttribute.LocalStorageEnabled,
            True
        )

        settings.setAttribute(
            QWebEngineSettings.WebAttribute.FullScreenSupportEnabled,
            True
        )

        settings.setAttribute(
            QWebEngineSettings.WebAttribute.JavascriptCanOpenWindows,
            True
        )

        settings.setAttribute(
            QWebEngineSettings.WebAttribute.JavascriptCanAccessClipboard,
            True
        )

        settings.setAttribute(
            QWebEngineSettings.WebAttribute.ErrorPageEnabled,
            True
        )

        settings.setAttribute(
            QWebEngineSettings.WebAttribute.PdfViewerEnabled,
            True
        )

        # ----------------------------------------------------
        # ADD WEBVIEW
        # ----------------------------------------------------

        self.layout.addWidget(self.webview)

        # ----------------------------------------------------
        # SIGNALS
        # ----------------------------------------------------

        self.webview.urlChanged.connect(
            self.on_url_changed
        )

        self.webview.titleChanged.connect(
            self.on_title_changed
        )

        self.webview.iconChanged.connect(
            self.on_icon_changed
        )

        self.webview.loadStarted.connect(
            self.on_load_started
        )

        self.webview.loadFinished.connect(
            self.on_load_finished
        )

        self.page.fullScreenRequested.connect(
            self.browser_window.handle_fullscreen
        )

        # ----------------------------------------------------
        # INITIAL PAGE
        # ----------------------------------------------------

        if url:
            self.load(url)
        else:
            self.load(
                QUrl("https://www.google.com")
            )

    def load(self, url):

        if isinstance(url, str):
            url = QUrl(url)

        self.webview.setUrl(url)

    def on_url_changed(self, url):

        if self.browser_window.current_browser() == self:
            self.browser_window.address_bar.setText(
                url.toString()
            )

    def on_title_changed(self, title):

        if not title:
            title = "New Tab"

        index = self.browser_window.tabs.indexOf(self)

        if index != -1:

            if len(title) > 24:
                title = title[:24] + "..."

            self.browser_window.tabs.setTabText(
                index,
                title
            )

    def on_icon_changed(self, icon):

        index = self.browser_window.tabs.indexOf(self)

        if index != -1 and not icon.isNull():

            self.browser_window.tabs.setTabIcon(
                index,
                icon
            )

    def on_load_started(self):

        self.browser_window.update_navigation_buttons()

    def on_load_finished(self, success):

        self.browser_window.update_navigation_buttons()


# ============================================================
# MAIN BROWSER
# ============================================================

class Browser(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle(APP_NAME)

        self.resize(
            1400,
            850
        )

        self.setMinimumSize(
            900,
            600
        )

        # ====================================================
        # WEB PROFILE
        # ====================================================

        self.profile = QWebEngineProfile(
            "NovaBrowser",
            self
        )

        self.profile.setPersistentCookiesPolicy(
            QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies
        )

        self.profile.setHttpCacheType(
            QWebEngineProfile.HttpCacheType.DiskHttpCache
        )

        self.profile.setPersistentStoragePath(
            str(DATA_DIR / "storage")
        )

        self.profile.setCachePath(
            str(DATA_DIR / "cache")
        )

        # ====================================================
        # TABS
        # ====================================================

        self.tabs = QTabWidget()

        self.tabs.setTabsClosable(True)
        self.tabs.setMovable(True)
        self.tabs.setDocumentMode(True)

        self.tabs.tabCloseRequested.connect(
            self.close_tab
        )

        self.tabs.currentChanged.connect(
            self.on_tab_changed
        )

        self.setCentralWidget(
            self.tabs
        )

        # ====================================================
        # TOOLBAR
        # ====================================================

        self.toolbar = QToolBar()

        self.toolbar.setMovable(False)

        self.toolbar.setIconSize(
            QSize(18, 18)
        )

        self.toolbar.setFixedHeight(
            58
        )

        self.addToolBar(
            self.toolbar
        )

        # ----------------------------------------------------
        # BACK
        # ----------------------------------------------------

        self.back_action = QAction(
            "←",
            self
        )

        self.back_action.setToolTip(
            "Back"
        )

        self.back_action.triggered.connect(
            self.go_back
        )

        self.toolbar.addAction(
            self.back_action
        )

        # ----------------------------------------------------
        # FORWARD
        # ----------------------------------------------------

        self.forward_action = QAction(
            "→",
            self
        )

        self.forward_action.setToolTip(
            "Forward"
        )

        self.forward_action.triggered.connect(
            self.go_forward
        )

        self.toolbar.addAction(
            self.forward_action
        )

        # ----------------------------------------------------
        # RELOAD
        # ----------------------------------------------------

        self.reload_action = QAction(
            "↻",
            self
        )

        self.reload_action.setToolTip(
            "Reload"
        )

        self.reload_action.triggered.connect(
            self.reload
        )

        self.toolbar.addAction(
            self.reload_action
        )

        # ----------------------------------------------------
        # HOME
        # ----------------------------------------------------

        self.home_action = QAction(
            "⌂",
            self
        )

        self.home_action.setToolTip(
            "Home"
        )

        self.home_action.triggered.connect(
            self.go_home
        )

        self.toolbar.addAction(
            self.home_action
        )

        self.toolbar.addSeparator()

        # ----------------------------------------------------
        # ADDRESS BAR
        # ----------------------------------------------------

        self.address_bar = QLineEdit()

        self.address_bar.setPlaceholderText(
            "Search or enter web address"
        )

        self.address_bar.setMinimumHeight(
            38
        )

        self.address_bar.returnPressed.connect(
            self.navigate
        )

        self.toolbar.addWidget(
            self.address_bar
        )

        # ----------------------------------------------------
        # FULLSCREEN
        # ----------------------------------------------------

        fullscreen_action = QAction(
            "⛶",
            self
        )

        fullscreen_action.setToolTip(
            "Fullscreen"
        )

        fullscreen_action.triggered.connect(
            self.toggle_fullscreen
        )

        self.toolbar.addAction(
            fullscreen_action
        )

        # ----------------------------------------------------
        # NEW TAB
        # ----------------------------------------------------

        new_tab_action = QAction(
            "+",
            self
        )

        new_tab_action.setToolTip(
            "New Tab"
        )

        new_tab_action.triggered.connect(
            self.new_tab
        )

        self.toolbar.addAction(
            new_tab_action
        )

        # ====================================================
        # STYLE
        # ====================================================

        self.setStyleSheet("""
            QMainWindow {
                background: #0c0e13;
            }

            QToolBar {
                background: #12151c;
                border: none;
                spacing: 5px;
                padding: 8px;
            }

            QToolButton {
                background: transparent;
                border: none;
                border-radius: 8px;
                color: #d5d9e2;
                font-size: 19px;
                padding: 7px;
            }

            QToolButton:hover {
                background: #222734;
            }

            QLineEdit {
                background: #1b1f29;
                border: 1px solid #2b3140;
                border-radius: 12px;
                padding: 0 14px;
                color: #f4f5f7;
                font-size: 14px;
            }

            QLineEdit:focus {
                border: 1px solid #527eff;
                background: #202530;
            }

            QTabWidget::pane {
                border: none;
                background: #0c0e13;
            }

            QTabBar {
                background: #0c0e13;
            }

            QTabBar::tab {
                background: #11141b;
                color: #858d9d;

                padding: 10px 8px 10px 16px;

                min-width: 130px;
                max-width: 230px;

                border: none;

                border-top-left-radius: 9px;
                border-top-right-radius: 9px;

                margin-right: 2px;
            }

            QTabBar::tab:selected {
                background: #1b1f29;
                color: white;
            }

            QTabBar::tab:hover {
                background: #181c25;
                color: white;
            }

            /* TAB CLOSE BUTTON */

            QTabBar::close-button {
                image: none;

                background: transparent;

                border: none;

                color: white;

                width: 18px;
                height: 18px;

                margin-left: 5px;
                margin-right: 2px;
            }

            QTabBar::close-button:hover {
                background: transparent;
                border: none;
            }

            QTabBar::close-button:pressed {
                background: transparent;
                border: none;
            }
        """)

        # ====================================================
        # CUSTOM TAB CLOSE BUTTONS
        # ====================================================

        self.tabs.tabBar().setStyleSheet("""
            QTabBar::tab {
                background: #11141b;
                color: #858d9d;

                padding: 10px 8px 10px 16px;

                min-width: 130px;
                max-width: 230px;

                border: none;

                border-top-left-radius: 9px;
                border-top-right-radius: 9px;

                margin-right: 2px;
            }

            QTabBar::tab:selected {
                background: #1b1f29;
                color: white;
            }

            QTabBar::tab:hover {
                background: #181c25;
                color: white;
            }

            QTabBar::close-button {
                background: transparent;
                border: none;
                color: white;
                width: 18px;
                height: 18px;
                margin-left: 5px;
            }

            QTabBar::close-button:hover {
                background: transparent;
                border: none;
            }
        """)

        # ====================================================
        # SHORTCUTS
        # ====================================================

        self.setup_shortcuts()

        # ====================================================
        # FIRST TAB
        # ====================================================

        self.new_tab()

    # ========================================================
    # SHORTCUTS
    # ========================================================

    def setup_shortcuts(self):

        shortcut_new = QShortcut(
            QKeySequence("Ctrl+T"),
            self
        )

        shortcut_new.activated.connect(
            self.new_tab
        )

        shortcut_close = QShortcut(
            QKeySequence("Ctrl+W"),
            self
        )

        shortcut_close.activated.connect(
            self.close_current_tab
        )

        shortcut_reload = QShortcut(
            QKeySequence("Ctrl+R"),
            self
        )

        shortcut_reload.activated.connect(
            self.reload
        )

        shortcut_focus = QShortcut(
            QKeySequence("Ctrl+L"),
            self
        )

        shortcut_focus.activated.connect(
            self.focus_address
        )

        shortcut_fullscreen = QShortcut(
            QKeySequence("F11"),
            self
        )

        shortcut_fullscreen.activated.connect(
            self.toggle_fullscreen
        )

        shortcut_back = QShortcut(
            QKeySequence("Alt+Left"),
            self
        )

        shortcut_back.activated.connect(
            self.go_back
        )

        shortcut_forward = QShortcut(
            QKeySequence("Alt+Right"),
            self
        )

        shortcut_forward.activated.connect(
            self.go_forward
        )

    # ========================================================
    # TABS
    # ========================================================

    def new_tab(self, url=None):

        tab = BrowserTab(
            self,
            url
        )

        index = self.tabs.addTab(
            tab,
            "New Tab"
        )

        self.tabs.setCurrentIndex(
            index
        )

        return tab

    def create_browser_page(self):

        tab = self.new_tab()

        return tab.page

    def close_tab(self, index):

        # Don't allow the browser to have zero tabs.
        if self.tabs.count() == 1:

            browser = self.current_browser()

            if browser:
                browser.load(
                    QUrl("https://www.google.com")
                )

            return

        widget = self.tabs.widget(
            index
        )

        self.tabs.removeTab(
            index
        )

        if widget:
            widget.deleteLater()

    def close_current_tab(self):

        index = self.tabs.currentIndex()

        if index >= 0:
            self.close_tab(
                index
            )

    def current_browser(self):

        widget = self.tabs.currentWidget()

        if isinstance(
            widget,
            BrowserTab
        ):
            return widget

        return None

    # ========================================================
    # NAVIGATION
    # ========================================================

    def navigate(self):

        text = self.address_bar.text().strip()

        if not text:
            return

        # ----------------------------------------------------
        # URL
        # ----------------------------------------------------

        if (
            text.startswith("http://")
            or text.startswith("https://")
            or text.startswith("file://")
        ):

            url = QUrl(text)

        # ----------------------------------------------------
        # DOMAIN
        # ----------------------------------------------------

        elif (
            "." in text
            and " " not in text
        ):

            url = QUrl(
                "https://" + text
            )

        # ----------------------------------------------------
        # GOOGLE SEARCH
        # ----------------------------------------------------

        else:

            encoded = (
                QUrl.toPercentEncoding(text)
                .data()
                .decode()
            )

            url = QUrl(
                "https://www.google.com/search?q="
                + encoded
            )

        browser = self.current_browser()

        if browser:
            browser.load(
                url
            )

    def go_back(self):

        browser = self.current_browser()

        if browser:
            browser.webview.back()

    def go_forward(self):

        browser = self.current_browser()

        if browser:
            browser.webview.forward()

    def reload(self):

        browser = self.current_browser()

        if browser:
            browser.webview.reload()

    def go_home(self):

        browser = self.current_browser()

        if browser:

            browser.load(
                QUrl(
                    "https://www.google.com"
                )
            )

    def focus_address(self):

        self.address_bar.setFocus()

        self.address_bar.selectAll()

    # ========================================================
    # TAB EVENTS
    # ========================================================

    def on_tab_changed(self, index):

        browser = self.current_browser()

        if not browser:
            return

        self.address_bar.setText(
            browser.webview.url().toString()
        )

        self.update_navigation_buttons()

    def update_navigation_buttons(self):

        browser = self.current_browser()

        if not browser:
            return

        self.back_action.setEnabled(
            browser.webview.history().canGoBack()
        )

        self.forward_action.setEnabled(
            browser.webview.history().canGoForward()
        )

    # ========================================================
    # FULLSCREEN
    # ========================================================

    def handle_fullscreen(self, request):

        request.accept()

        if request.toggleOn():

            self.showFullScreen()

            self.toolbar.hide()
            self.tabs.tabBar().hide()

        else:

            self.showNormal()

            self.toolbar.show()
            self.tabs.tabBar().show()

    def toggle_fullscreen(self):

        if self.isFullScreen():

            self.showNormal()

            self.toolbar.show()
            self.tabs.tabBar().show()

        else:

            self.showFullScreen()

            self.toolbar.hide()
            self.tabs.tabBar().hide()

    # ========================================================
    # CLOSE
    # ========================================================

    def closeEvent(self, event):

        event.accept()


# ============================================================
# APPLICATION
# ============================================================

def main():

    QApplication.setAttribute(
        Qt.ApplicationAttribute.AA_ShareOpenGLContexts
    )

    app = QApplication(
        sys.argv
    )

    app.setApplicationName(
        APP_NAME
    )

    app.setApplicationDisplayName(
        APP_NAME
    )

    app.setStyle(
        "Fusion"
    )

    browser = Browser()

    browser.show()

    sys.exit(
        app.exec()
    )


# ============================================================
# START
# ============================================================

if __name__ == "__main__":
    main()