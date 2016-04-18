"""
Flask Documentation:     http://flask.pocoo.org/docs/
Jinja2 Documentation:    http://jinja.pocoo.org/2/documentation/
Werkzeug Documentation:  http://werkzeug.pocoo.org/documentation/

This file creates your application.
"""

from app import app
from flask import render_template, request, redirect, url_for, jsonify

from httplib import HTTPException
from operator import attrgetter
from Models import Question, Answer
from Database import db
import QuestionMatcher as matcher

#defining URL stuff and populating the html pages
#Have to make the html page more prettier
@app.route('/', methods=['GET']) #The index page
def index():
    questions = Question.query.all()
    questions = sorted(questions, key=attrgetter('timestamp'), reverse=True) #sorting the questions based on time which is generated everytime someone posts something

    top_answers = {}
    answer_count = {}
    for question in questions:
        answers = Answer.query.filter_by(question_id=question.id).all()
        answer_count[question.id] = len(answers)
        if len(answers) > 0:
            top_answer = max(answers, key=attrgetter('upvote_count'))
            top_answers[question.id] = top_answer
    return render_template('index.html', questions=questions, top_answers=top_answers, answer_count=answer_count)


@app.route('/question/<int:question_id>', methods=['GET'])
def question(question_id):
    question = Question.query.get(question_id)
    question.views += 1
    db.session.commit()
    answers = Answer.query.filter_by(question_id=question.id).all()
    answers = sorted(answers, key=attrgetter('upvote_count'), reverse=True)
    return render_template('question.html', question=question, answers=answers)


@app.route('/ask', methods=['GET', 'POST'])
def ask():
    if request.method == 'POST':
        subject = request.form['question_subject']
        body = request.form['question_body']
        question = Question(subject, body)
        db.session.add(question)
        db.session.commit()
        return flask.redirect('/')
    else:
        return render_template('ask.html')


@app.route('/answer/<int:question_id>', methods=['POST'])
def answer(question_id):
    question = Question.query.get(question_id)
    body = request.form['answer_body']
    answer = Answer(question.id, body)
    db.session.add(answer)
    db.session.commit()
    return flask.redirect('/question/' + str(question_id))


@app.route('/api/question/<int:question_id>', methods=['GET'])
def api_question(question_id):
    question = Question.query.get(question_id)
    return jsonify({"question_id":question.id, "subject":question.subject})


@app.route('/api/upvote/<int:answer_id>', methods=['GET', 'POST'])
def upvote(answer_id):
    answer = Answer.query.get(answer_id)
    if answer is None:
        return make_json_error(500)

    if request.method == 'POST':
        answer.upvote_count += 1
        db.session.commit()
        return jsonify({'success': True, 'new_total': answer.upvote_count}), 200, {'ContentType': 'application/json'}
    else:
        return jsonify(upvote_count=answer.upvote_count)


@app.route('/api/matchscore', methods=['GET'])
def get_match_score():
    subject = request.args.get('subject')
    match_score = matcher.get_match_scores(subject)
    return jsonify({"matchscore":match_score})


@app.route('/reset', methods=['GET'])
def reset():
    Question.query.delete()
    Answer.query.delete()
    db.session.commit()
    return flask.redirect('/')


def make_json_error(ex):
    response = jsonify(message=str(ex))
    response.status_code = (ex.code
                            if isinstance(ex, HTTPException)
                            else 500)
    return response



###
# Routing for your application.
###

@app.route('/about/')
def about():
    """Render the website's about page."""
    return render_template('about.html')


###
# The functions below should be applicable to all Flask apps.
###

@app.route('/<file_name>.txt')
def send_text_file(file_name):
    """Send your static text file."""
    file_dot_text = file_name + '.txt'
    return app.send_static_file(file_dot_text)


@app.after_request
def add_header(response):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    response.headers['X-UA-Compatible'] = 'IE=Edge,chrome=1'
    response.headers['Cache-Control'] = 'public, max-age=600'
    return response


@app.errorhandler(404)
def page_not_found(error):
    """Custom 404 page."""
    return render_template('404.html'), 404


if __name__ == '__main__':
    app.run(debug=True,host="0.0.0.0",port="8888")
