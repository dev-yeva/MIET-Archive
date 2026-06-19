using System.Collections.ObjectModel;
using System.Linq;
using System.Windows.Input;
using lab6.Models;

namespace lab6.ViewModels;

public class MainViewModel : BaseViewModel
{
    public ObservableCollection<TaskItem> Tasks { get; set; }

    private ObservableCollection<TaskItem> filteredTasks;

    public ObservableCollection<TaskItem> FilteredTasks
    {
        get => filteredTasks;
        set
        {
            filteredTasks = value;
            OnPropertyChanged(); // уведомляет экран об изменении
        }
    }

    private TaskItem? selectedTask;

    public TaskItem? SelectedTask
    {
        get => selectedTask;
        set
        {
            selectedTask = value;
            OnPropertyChanged();
        }
    }

    private string filter = "Все";

    public string Filter
    {
        get => filter;
        set
        {
            filter = value;
            OnPropertyChanged();

            ApplyFilter();
        }
    }

    public ICommand AddCommand { get; }

    public MainViewModel()
    {
        Tasks = new ObservableCollection<TaskItem>();

        FilteredTasks = new ObservableCollection<TaskItem>();

        AddCommand = new RelayCommand(AddTask);
    }

    private void AddTask()
    {
        var task = new TaskItem
        {
            Title = "Новая задача",
            Status = "Новая"
        };

        Tasks.Add(task);

        ApplyFilter();

        SelectedTask = task;
    }

    private void ApplyFilter()
    {
        FilteredTasks.Clear();

        var items = Filter == "Все"
            ? Tasks  // берём все задачи
            : new ObservableCollection<TaskItem>( // только с нужным статусом
                Tasks.Where(t => t.Status == Filter));

        foreach (var item in items)
        {
            FilteredTasks.Add(item);
        }
    }
}