using System;
using System.Collections.Generic;
using System.Reactive;
using System.Text;
using Avalonia.Controls;
using Avalonia.Dialogs;
using Avalonia.Input;
using Avalonia.Platform;
using MessageBox.Avalonia.Enums;
using MiniMvvm;
using ReactiveUI;
//using System.Windows.Forms;

namespace HostsManager.ViewModels
{
 
    //[DataContract]
    public class MainWindowViewModel : ViewModelBase
    {
//        private bool _isMenuItemChecked = true;
        private WindowState _windowState;
        private WindowState[] _windowStates;
//        private int _transparencyLevel;
//        private ExtendClientAreaChromeHints _chromeHints;
//        private bool _extendClientAreaEnabled;
//        private bool _systemTitleBarEnabled;
//        private bool _preferSystemChromeEnabled;
//        private double _titleBarHeight;

//        public RelayCommand<ICloseable> CloseWindowCommand { get; private set; }
        //[Reactive, DataMember]
        public string Greeting
        {
            get => "Welcome to Avalonia from VSCode!";
            set => throw new NotImplementedException();
        }

        public MainWindowViewModel() {
            AboutCommand = MiniCommand.CreateFromTask(async () =>
            {
                var dialog = new AboutAvaloniaDialog();

//                var mainWindow = (App.Current.ApplicationLifetime as IClassicDesktopStyleApplicationLifetime)?.MainWindow;

                await dialog.ShowDialog(this);
//                await dialog.ShowDialog(mainWindow);
            });

            ExitCommand = MiniCommand.Create(() =>
            {
                (App.Current.ApplicationLifetime as IClassicDesktopStyleApplicationLifetime).Shutdown();
            });

//            this.CloseWindowCommand = new RelayCommand<ICloseable>(this.CloseWindow);
            MenuCommand = ReactiveCommand.Create<string>(RunMenu);
            //var MenuCommandExit = ReactiveCommand.Create<string>(this.CloseWindow());
        }

        private void CloseWindow(Window curwindow) {
            if (curwindow != null) {
                curwindow.Close();
            }
        }

        public WindowState WindowState
        {
            get { return _windowState; }
            set { this.RaiseAndSetIfChanged(ref _windowState, value); }
        }

        public WindowState[] WindowStates
        {
            get { return _windowStates; }
            set { this.RaiseAndSetIfChanged(ref _windowStates, value); }
        }

        public ReactiveCommand<string, System.Reactive.Unit> MenuCommand { get; }

        void RunMenu(string param) {
            // Process menus
            var msgAlert = MessageBox.Avalonia.MessageBoxManager.GetMessageBoxStandardWindow("Alert", param, ButtonEnum.Ok, Icon.Warning);

            switch (param) {
            case "Open":
            // Open file:  var lines = File.ReadAllLines("pathToFile.txt");
            case "Save":
            case "Cut":
            case "Copy":
            case "Paste":
                msgAlert.Show();
                break;
            case "Exit":
//                Window.Close(this);
                break;
            }
        }

        public MiniCommand AboutCommand { get; }

        public MiniCommand ExitCommand { get; }
    }
}
