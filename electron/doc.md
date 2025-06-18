Custom Title Bar
Basic tutorial
Application windows have a default chrome applied by the OS. Not to be confused with the Google Chrome browser, window chrome refers to the parts of the window (e.g. title bar, toolbars, controls) that are not a part of the main web content. While the default title bar provided by the OS chrome is sufficient for simple use cases, many applications opt to remove it. Implementing a custom title bar can help your application feel more modern and consistent across platforms.

You can follow along with this tutorial by opening Fiddle with the following starter code.

docs/fiddles/features/window-customization/custom-title-bar/starter-code (36.4.0)
main.js
const { app, BrowserWindow } = require('electron')

function createWindow () {
  const win = new BrowserWindow({})
  win.loadURL('https://example.com')
}

app.whenReady().then(() => {
  createWindow()
})

Remove the default title bar
Let’s start by configuring a window with native window controls and a hidden title bar. To remove the default title bar, set the BaseWindowContructorOptions titleBarStyle param in the BrowserWindow constructor to 'hidden'.

docs/fiddles/features/window-customization/custom-title-bar/remove-title-bar (36.4.0)
main.js
const { app, BrowserWindow } = require('electron')

function createWindow () {
  const win = new BrowserWindow({
    // remove the default titlebar
    titleBarStyle: 'hidden'
  })
  win.loadURL('https://example.com')
}

app.whenReady().then(() => {
  createWindow()
})

Add native window controls Windows Linux
On macOS, setting titleBarStyle: 'hidden' removes the title bar while keeping the window’s traffic light controls available in the upper left hand corner. However on Windows and Linux, you’ll need to add window controls back into your BrowserWindow by setting the BaseWindowContructorOptions titleBarOverlay param in the BrowserWindow constructor.

docs/fiddles/features/window-customization/custom-title-bar/native-window-controls (36.4.0)
main.js
const { app, BrowserWindow } = require('electron')

function createWindow () {
  const win = new BrowserWindow({
    // remove the default titlebar
    titleBarStyle: 'hidden',
    // expose window controls in Windows/Linux
    ...(process.platform !== 'darwin' ? { titleBarOverlay: true } : {})
  })
  win.loadURL('https://example.com')
}

app.whenReady().then(() => {
  createWindow()
})

Setting titleBarOverlay: true is the simplest way to expose window controls back into your BrowserWindow. If you’re interested in customizing the window controls further, check out the sections Custom traffic lights and Custom window controls that cover this in more detail.

Create a custom title bar
Now, let’s implement a simple custom title bar in the webContents of our BrowserWindow. There’s nothing fancy here, just HTML and CSS!

docs/fiddles/features/window-customization/custom-title-bar/custom-title-bar (36.4.0)
main.js
index.html
styles.css
const { app, BrowserWindow } = require('electron')

function createWindow () {
  const win = new BrowserWindow({
    // remove the default titlebar
    titleBarStyle: 'hidden',
    // expose window controls in Windows/Linux
    ...(process.platform !== 'darwin' ? { titleBarOverlay: true } : {})
  })

  win.loadFile('index.html')
}

app.whenReady().then(() => {
  createWindow()
})

Currently our application window can’t be moved. Since we’ve removed the default title bar, the application needs to tell Electron which regions are draggable. We’ll do this by adding the CSS style app-region: drag to the custom title bar. Now we can drag the custom title bar to reposition our app window!

docs/fiddles/features/window-customization/custom-title-bar/custom-drag-region (36.4.0)
main.js
index.html
styles.css
const { app, BrowserWindow } = require('electron')

function createWindow () {
  const win = new BrowserWindow({
    // remove the default titlebar
    titleBarStyle: 'hidden',
    // expose window controls in Windows/Linux
    ...(process.platform !== 'darwin' ? { titleBarOverlay: true } : {})
  })

  win.loadFile('index.html')
}

app.whenReady().then(() => {
  createWindow()
})

For more information around how to manage drag regions defined by your electron application, see the Custom draggable regions section below.

Congratulations, you've just implemented a basic custom title bar!

Advanced window customization
Custom traffic lights macOS
Customize the look of your traffic lights macOS
The customButtonsOnHover title bar style will hide the traffic lights until you hover over them. This is useful if you want to create custom traffic lights in your HTML but still use the native UI to control the window.

const { BrowserWindow } = require('electron')
const win = new BrowserWindow({ titleBarStyle: 'customButtonsOnHover' })

Customize the traffic light position macOS
To modify the position of the traffic light window controls, there are two configuration options available.

Applying hiddenInset title bar style will shift the vertical inset of the traffic lights by a fixed amount.

main.js
const { BrowserWindow } = require('electron')
const win = new BrowserWindow({ titleBarStyle: 'hiddenInset' })

If you need more granular control over the positioning of the traffic lights, you can pass a set of coordinates to the trafficLightPosition option in the BrowserWindow constructor.

main.js
const { BrowserWindow } = require('electron')
const win = new BrowserWindow({
  titleBarStyle: 'hidden',
  trafficLightPosition: { x: 10, y: 10 }
})

Show and hide the traffic lights programmatically macOS
You can also show and hide the traffic lights programmatically from the main process. The win.setWindowButtonVisibility forces traffic lights to be show or hidden depending on the value of its boolean parameter.

main.js
const { BrowserWindow } = require('electron')
const win = new BrowserWindow()
// hides the traffic lights
win.setWindowButtonVisibility(false)

note
Given the number of APIs available, there are many ways of achieving this. For instance, combining frame: false with win.setWindowButtonVisibility(true) will yield the same layout outcome as setting titleBarStyle: 'hidden'.

Custom window controls
The Window Controls Overlay API is a web standard that gives web apps the ability to customize their title bar region when installed on desktop. Electron exposes this API through the titleBarOverlay option in the BrowserWindow constructor. When titleBarOverlay is enabled, the window controls become exposed in their default position, and DOM elements cannot use the area underneath this region.

note
titleBarOverlay requires the titleBarStyle param in the BrowserWindow constructor to have a value other than default.

The custom title bar tutorial covers a basic example of exposing window controls by setting titleBarOverlay: true. The height, color (Windows Linux), and symbol colors (Windows) of the window controls can be customized further by setting titleBarOverlay to an object.

The value passed to the height property must be an integer. The color and symbolColor properties accept rgba(), hsla(), and #RRGGBBAA color formats and support transparency. If a color option is not specified, the color will default to its system color for the window control buttons. Similarly, if the height option is not specified, the window controls will default to the standard system height:

main.js
const { BrowserWindow } = require('electron')
const win = new BrowserWindow({
  titleBarStyle: 'hidden',
  titleBarOverlay: {
    color: '#2f3241',
    symbolColor: '#74b1be',
    height: 60
  }
})

note
Once your title bar overlay is enabled from the main process, you can access the overlay's color and dimension values from a renderer using a set of readonly JavaScript APIs and CSS Environment Variables.

Custom Window Interactions
Custom draggable regions
By default, windows are dragged using the title bar provided by the OS chrome. Apps that remove the default title bar need to use the app-region CSS property to define specific areas that can be used to drag the window. Setting app-region: drag marks a rectagular area as draggable.

It is important to note that draggable areas ignore all pointer events. For example, a button element that overlaps a draggable region will not emit mouse clicks or mouse enter/exit events within that overlapping area. Setting app-region: no-drag reenables pointer events by excluding a rectagular area from a draggable region.

To make the whole window draggable, you can add app-region: drag as body's style:

styles.css
body {
  app-region: drag;
}

And note that if you have made the whole window draggable, you must also mark buttons as non-draggable, otherwise it would be impossible for users to click on them:

styles.css
button {
  app-region: no-drag;
}

If you're only setting a custom title bar as draggable, you also need to make all buttons in title bar non-draggable.

Tip: disable text selection
When creating a draggable region, the dragging behavior may conflict with text selection. For example, when you drag the title bar, you may accidentally select its text contents. To prevent this, you need to disable text selection within a draggable area like this:

.titlebar {
  user-select: none;
  app-region: drag;
}

Tip: disable context menus
On some platforms, the draggable area will be treated as a non-client frame, so when you right click on it, a system menu will pop up. To make the context menu behave correctly on all platforms, you should never use a custom context menu on draggable areas.

Click-through windows
To create a click-through window, i.e. making the window ignore all mouse events, you can call the win.setIgnoreMouseEvents(ignore) API:

main.js
const { BrowserWindow } = require('electron')
const win = new BrowserWindow()
win.setIgnoreMouseEvents(true)

Forward mouse events macOS Windows
Ignoring mouse messages makes the web contents oblivious to mouse movement, meaning that mouse movement events will not be emitted. On Windows and macOS, an optional parameter can be used to forward mouse move messages to the web page, allowing events such as mouseleave to be emitted:

main.js
const { BrowserWindow, ipcMain } = require('electron')
const path = require('node:path')

const win = new BrowserWindow({
  webPreferences: {
    preload: path.join(__dirname, 'preload.js')
  }
})

ipcMain.on('set-ignore-mouse-events', (event, ignore, options) => {
  const win = BrowserWindow.fromWebContents(event.sender)
  win.setIgnoreMouseEvents(ignore, options)
})

preload.js
window.addEventListener('DOMContentLoaded', () => {
  const el = document.getElementById('clickThroughElement')
  el.addEventListener('mouseenter', () => {
    ipcRenderer.send('set-ignore-mouse-events', true, { forward: true })
  })
  el.addEventListener('mouseleave', () => {
    ipcRenderer.send('set-ignore-mouse-events', false)
  })
})

This makes the web page click-through when over the #clickThroughElement element, and returns to normal outside it.

Edit this page


Custom Window Styles
Frameless windows
Frameless Window

A frameless window removes all chrome applied by the OS, including window controls.

To create a frameless window, set the BaseWindowContructorOptions frame param in the BrowserWindow constructor to false.

docs/fiddles/features/window-customization/custom-window-styles/frameless-windows (36.4.0)
main.js
const { app, BrowserWindow } = require('electron')

function createWindow () {
  const win = new BrowserWindow({
    width: 300,
    height: 200,
    frame: false
  })
  win.loadURL('https://example.com')
}

app.whenReady().then(() => {
  createWindow()
})

Transparent windows
Transparent Window Transparent Window in macOS Mission Control

To create a fully transparent window, set the BaseWindowContructorOptions transparent param in the BrowserWindow constructor to true.

The following fiddle takes advantage of a transparent window and CSS styling to create the illusion of a circular window.

docs/fiddles/features/window-customization/custom-window-styles/transparent-windows (36.4.0)
main.js
index.html
styles.css
const { app, BrowserWindow } = require('electron')

function createWindow () {
  const win = new BrowserWindow({
    width: 100,
    height: 100,
    resizable: false,
    frame: false,
    transparent: true
  })
  win.loadFile('index.html')
}

app.whenReady().then(() => {
  createWindow()
})

Limitations
You cannot click through the transparent area. See #1335 for details.
Transparent windows are not resizable. Setting resizable to true may make a transparent window stop working on some platforms.
The CSS blur() filter only applies to the window's web contents, so there is no way to apply blur effect to the content below the window (i.e. other applications open on the user's system).
The window will not be transparent when DevTools is opened.
On Windows:
Transparent windows can not be maximized using the Windows system menu or by double clicking the title bar. The reasoning behind this can be seen on PR #28207.
On macOS:
The native window shadow will not be shown on a transparent window.