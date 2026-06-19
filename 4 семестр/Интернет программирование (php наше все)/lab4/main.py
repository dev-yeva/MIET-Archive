from flask import Flask, render_template, redirect, url_for

app = Flask(__name__)

jokes = {
    1: "Программисты путают Хэллоуин и Рождество, потому что OCT 31 = DEC 25.",
    2: "Есть 10 типов людей: те, кто понимает двоичный код, и те, кто нет.",
    3: "Роботы едят пиццу по одному байту за раз.",
    4: "Один монитор — обычный программист, два — продвинутый программист, три — системный программист, четыре — охранник.",
    5: "Программисты не любят природу, потому что там слишком много багов.",
    6: "Программист выключает компьютер комбинацией Ctrl + Alt + Delete → Enter.",
    7: "На вопрос «Ты понял задачу?» программист отвечает: «Почти скомпилировал».",
}


@app.route("/")
def index():
    return redirect(url_for("show_page", page_number=1))


@app.route("/<int:page_number>")
def show_page(page_number):
    if 1 <= page_number <= len(jokes):
        joke = jokes.get(page_number)
        return render_template(
            "joke.html", page_number=page_number, joke=joke, joke_count=len(jokes)
        )
    else:
        return "Страница не найдена", 404


if __name__ == "__main__":
    app.run()


