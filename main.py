from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests

db = SQLAlchemy()
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///movies.db'
db.init_app(app)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap5(app)

API_KEY = '2c98c8964ffa461edcc829243ecee47a'
MOVIE_DB_DETAILS = 'https://api.themoviedb.org/3/movie'
MOVIE_DB_IMG = "https://image.tmdb.org/t/p/w500"


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String)
    rating = db.Column(db.Integer, nullable=False)
    ranking = db.Column(db.Integer, nullable=False)
    review = db.Column(db.Integer)
    img_url = db.Column(db.String, nullable=False)


class EditForm(FlaskForm):
    rating = StringField('Your Rating Out of 10', validators=[DataRequired()])
    review = StringField('Your Review', validators=[DataRequired()])
    submit = SubmitField('Submit')


class AddForm(FlaskForm):
    title = StringField('Movie Title', validators=[DataRequired()])
    submit = SubmitField('Submit')


@app.route("/")
def home():
    movies = db.session.execute(db.select(Movie).order_by(Movie.rating)).scalars().all()
    for i in range(len(movies)):
        movies[i].ranking = len(movies) - i
    db.session.commit()
    return render_template("index.html", movies=movies)


@app.route("/add", methods=['POST', 'GET'])
def add():
    form = AddForm()
    if form.validate_on_submit():
        title = form.title.data
        url = f"https://api.themoviedb.org/3/search/movie?api_key={API_KEY}&query={title}" \
              f"&include_adult=true&language=en-US"
        response = requests.get(url)
        return render_template("select.html", selection=response.json()['results'])
    return render_template("add.html", form=form)


@app.route("/edit", methods=['POST', 'GET'])
def edit():
    form = EditForm()
    if form.validate_on_submit():
        movie_id = request.args.get('movie_id')
        movie_selected = db.get_or_404(Movie, movie_id)
        movie_selected.rating = form.rating.data
        movie_selected.review = form.review.data
        db.session.commit()
        return redirect(url_for("home"))
    return render_template("edit.html", form=form)


@app.route("/find")
def find():
    movie_api_id = request.args.get("movie_id")
    url = f"{MOVIE_DB_DETAILS}/{movie_api_id}"
    response = requests.get(url, params={"api_key": API_KEY, "language": "en-US"}).json()
    new_movie = Movie(
        title=response['title'],
        year=response["release_date"].split("-")[0],
        description=response["overview"],
        rating=0,
        ranking=10,
        review="* To Be Reviewed *",
        img_url=f"{MOVIE_DB_IMG}{response['poster_path']}"
    )
    db.session.add(new_movie)
    db.session.commit()
    return redirect(url_for("edit", movie_id=new_movie.id))


@app.route("/delete")
def delete():
    movie_id = request.args.get('movie_id')
    movie_selected = db.get_or_404(Movie, movie_id)
    db.session.delete(movie_selected)
    db.session.commit()
    return redirect(url_for("home"))


if __name__ == '__main__':
    app.run(debug=True)
