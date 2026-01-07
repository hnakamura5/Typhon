# uv run -m script.test *> .\private\test.log
# at project root


from .all import test_all

if __name__ == "__main__":
    test_all()
