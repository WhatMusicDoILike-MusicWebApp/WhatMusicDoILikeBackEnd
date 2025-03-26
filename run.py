from app import create_app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
else:
    gunicorn_app = create_app()