using System;
using System.Runtime.InteropServices;
using Avalonia;
using Avalonia.Controls;
using Avalonia.Input;
using Avalonia.Markup.Xaml;
using HostsManager.ViewModels;

namespace HostsManager.Views
{
    public class MainWindow : Window, ICloseable
    {
        private NativeMenu _recentMenu;

        public MainWindow()
        {
            InitializeComponent();
#if DEBUG
            this.AttachDevTools();
#endif
            _recentMenu = ((NativeMenu.GetMenu(this).Items[0] as NativeMenuItem)?.Menu.Items[2] as NativeMenuItem)?.Menu;
        }

        public static string MenuQuitHeader => RuntimeInformation.IsOSPlatform(OSPlatform.OSX) ? "Quit HostsManager" : "E_xit";

        public static KeyGesture MenuQuitGesture => RuntimeInformation.IsOSPlatform(OSPlatform.OSX) ?
            new KeyGesture(Key.Q, KeyModifiers.Meta) :
            new KeyGesture(Key.F4, KeyModifiers.Alt);

        public void OnOpenClicked(object sender, EventArgs args)
        {
            _recentMenu.Items.Insert(0, new NativeMenuItem("Item " + (_recentMenu.Items.Count + 1)));
        }

        public void OnSaveClicked(object sender, EventArgs args)
        {
            //_recentMenu.Items.Insert(0, new NativeMenuItem("Item " + (_recentMenu.Items.Count + 1)));
        }

        public void OnCloseClicked(object sender, EventArgs args)
        {
            Close();
        }

        private void InitializeComponent()
        {
            AvaloniaXamlLoader.Load(this);
        }

        public interface ICloseable {
            void Close();
        }
    }
}
