from .app import create_app
#For sites such as Render
app = create_app()
if __name__ == "__main__":
    app.run(debug=True) 