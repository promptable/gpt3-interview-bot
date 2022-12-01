# GPT3 Interview Bot

Give yourself practice interviews with GPT3. Paste in Resume, Question, get interviewed, and receive feedback.

Try it at: http://gpt-interview-bot.fly.dev


## Setup

Requires Python 3.6+. Tested on Mac M1 Python 3.9.

1. Create an account with OpenAI and add your API key to `.env.secrets`

2. Install python requirements.

```bash
# Ensure you're using python 3.6+
python3 --version

# Uses your default python environment
pip3 install -r requirements.txt

# Alternatively, create a virtual environment (recommended)
pip3 install virtualenv
virtualenv .venv --python python3
source .venv/bin/activate
pip3 install -r requirements.txt
```

NOTE: If you're on Mac M1, and get stuck installing gevent / grpcio, try this:

```bash
pip3 install --no-cache-dir --upgrade --force-reinstall -Iv grpcio gevent

pip3 install -r requirements.txt
```

3. Run streamlit

```bash
# Run the streamlit app
streamlit run interview_streamlit.py

# Should open a new tab in your browser at
http://localhost:8501/

# If running on remote box (EC2, etc). Expose the port, then:
streamlit run --server.headless true interview_streamlit.py --server.port 8502
```

## Adding passwords

Do this to get password protection. (Also need to wrap main() call in the password check)

```bash
# .streamlit/secrets.toml
password = "yourpassword"
```

## Deploy

Deploy using Docker and Fly.io
- https://docs.streamlit.io/knowledge-base/tutorials/deploy/docker
- https://fly.io/docs/reference/secrets/#setting-secrets

```bash
fly launch
fly deploy --local-only
```
