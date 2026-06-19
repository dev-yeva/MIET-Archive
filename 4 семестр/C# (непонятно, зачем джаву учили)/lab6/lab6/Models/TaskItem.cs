using System.ComponentModel;
using System.Runtime.CompilerServices;

namespace lab6.Models;

public class TaskItem : INotifyPropertyChanged
{
    private string? title;
    private string? status;

    public string? Title
    {
        get => title;
        set
        {
            title = value;
            OnPropertyChanged();
        }
    }

    public string? Status
    {
        get => status;
        set
        {
            status = value;
            OnPropertyChanged();
        }
    }

    public event PropertyChangedEventHandler? PropertyChanged;

    protected void OnPropertyChanged([CallerMemberName] string? name = null)
    {
        PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(name));
    }
}