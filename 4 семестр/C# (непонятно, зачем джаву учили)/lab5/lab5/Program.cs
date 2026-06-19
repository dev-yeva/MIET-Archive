using System;
using System.Collections.Generic;
using System.Collections.Concurrent;
using System.Threading;
using System.Threading.Tasks;

class Program
{
    static ConcurrentDictionary<string, Task<int>> cache = new();

    static Random rnd = new Random();

    static async Task Main()
    {
        //await Task1();
        //await Task2();
        await Task3();
    }

    static async Task Task1()
    {
        Console.WriteLine("Задание 1. SemaphoreSlim");

        SemaphoreSlim sem = new SemaphoreSlim(3);
        List<Task> list = new List<Task>();

        for (int i = 1; i <= 500; i++)
        {
            var x = i;
            list.Add(Task.Run(async () =>
            {
                await sem.WaitAsync();
                 
                Console.WriteLine("Старт задачи " + x);

                await Task.Delay(rnd.Next(100, 501));

                Console.WriteLine("Конец задачи " + x);

                sem.Release();
            }));
        }

        await Task.WhenAll(list);
    }

    static async Task Task2()
    {
        Console.WriteLine("\nЗадание 2. Паттерн «Повтор»");

        var cts = new CancellationTokenSource();

        int result = await ExecuteWithRetry<int>(
            async (token) =>
            {
                await Task.Delay(500, token);

                if (rnd.Next(2) == 0)
                    throw new Exception("Ошибка");

                return 123;
            },
            3,
            cts.Token
        );

        Console.WriteLine("Результат: " + result);
    }

    static async Task<T> ExecuteWithRetry<T>(
         Func<CancellationToken, Task<T>> operation,
         int maxAttempts,
         CancellationToken token)
    {
        int delay = 1000;

        for (int attempt = 1; attempt <= maxAttempts; attempt++)
        {
            try
            {
                return await operation(token);
            }
            catch
            {
                Console.WriteLine($"Ошибка, попытка {attempt}");

                if (attempt == maxAttempts)
                    throw;

                await Task.Delay(delay, token);
                delay *= 2;
            }
        }

        throw new Exception();
    }

    
    static async Task Task3()
    {
        Console.WriteLine("\nЗадание 3. Асинхронный атомарный кэш");

        List<Task> list = new List<Task>();

        for (int i = 1; i <= 20; i++)
        {
            int x = i;

            list.Add(Task.Run(async () =>
            {
                Console.WriteLine("Поток " + x);

                int n = await GetData();

                Console.WriteLine("Результат " + n);
            }));
        }

        await Task.WhenAll(list);
    }

    static Task<int> GetData()
    {
        return cache.GetOrAdd("key", Heavy());
    }

    static async Task<int> Heavy()
    {
        Console.WriteLine("Тяжёлый расчёт");

        await Task.Delay(2000);

        return CountPrimes(10000, 11000);
    }

    static int CountPrimes(int a, int b)
    {
        int count = 0;

        for (int i = a; i <= b; i++)
            if (Prime(i)) count++;

        return count;
    }

    static bool Prime(int n)
    {
        if (n < 2) return false;

        for (int i = 2; i < n; i++)
            if (n % i == 0) return false;

        return true;
    }
}