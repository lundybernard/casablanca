# Casablanca

**Casablanca** is a Python package designed to record and replay messages from/to RabbitMQ. Primarily intended as a developer tool for automated testing, Casablanca can also be used to populate RabbitMQ queues with data from static files for application or production use.

---

## Features

Casablanca provides the following key features:

- Record messages from one or more RabbitMQ queues.
- Replay recorded messages to RabbitMQ queues.
- Seamlessly integrate into automated testing workflows and CI/CD pipelines.
- Populate RabbitMQ queues in production or application code from static files.
- Command-line interface (CLI) for easy usage.
- Python API for advanced integrations within custom workflows.
- Flexible configuration options for RabbitMQ and file handling.

---

## Prerequisites

You will need the following before using Casablanca:

- Python 3.7 or higher
- RabbitMQ installed and running
- `pip` for Python package management

---

## Installation

Casablanca uses `pyproject.toml` (PEP 517/518) for building and installing.

### Installing Casablanca in Development Mode

Clone the repository and install in editable mode:

```bash
git clone https://github.com/your-repo/casablanca.git
cd casablanca
pip install -e .
```

### Installing Casablanca for Production

For a standard production installation:

```bash
pip install .
```

---

## Usage

Casablanca supports recording and replaying RabbitMQ messages either via its **Command-Line Interface (CLI)** or as a **Python API** for more advanced use-cases.

### Recording Messages

Use Casablanca to record messages from RabbitMQ queues. Messages can be stored in a variety of formats (e.g., log files, JSON).

#### Example CLI Usage for Recording

```bash
casablanca record --queue my-queue --output messages.log --host localhost --port 5672
```

This command connects to RabbitMQ, listens to the `my-queue`, and records all messages into `messages.log`.

### Replaying Messages

Replay stored messages back into RabbitMQ queues. This is helpful for testing workflows or initializing queues from predefined data.

#### Example CLI Usage for Replaying

```bash
casablanca replay --input messages.log --queue replay-queue --host localhost --port 5672
```

This replays all the messages saved in `messages.log` into the specified RabbitMQ `replay-queue`.

---

## Configuration

Casablanca allows configuration via:

1. **Command-line arguments** (e.g., `--host`, `--queue`, `--output`)
2. **Environment variables** (e.g., `RABBITMQ_HOST`, `RABBITMQ_PORT`)
3. **Configuration files** (e.g., `config.yaml` or `config.json`).

---

## Testing

Casablanca includes both **unit tests** and **functional tests** to ensure correctness and reliability. Testing is an integral part of the source code, with unit tests existing alongside the implementation they validate.

### Running Unit Tests

Unit tests exist side-by-side with the code they test. For example:
/casablanca/ 
    recorder.py  # Implementation Code
    replayer.py  
        tests/
            recorder_test.py  # Unit Tests for recorder.py
            replayer_test.py  # Unit Tests for replayer.py



Run unit tests by simply running `pytest` over the source code directory:

```bash
pytest casablanca/
```

Unit tests do not require a running RabbitMQ instance and are limited to verifying the internal logic and behavior of individual components.

### Running Functional Tests

Functional tests validate the interaction of Casablanca with an active RabbitMQ server. These tests ensure that messages can be correctly recorded and replayed.

Run functional tests with:

```bash
pytest functional_tests/
```

Make sure RabbitMQ is running locally before executing functional tests.

### Running All Tests

To run both unit tests and functional tests together:

```bash
pytest
```

### Containerized Tests (Optional)

For testing Casablanca in containerized environments, you can use Docker:

```bash
docker-compose build
docker-compose up
pytest
```

#### CLI Shortcut for Container Tests

You can also run containerized tests via a CLI command:

```bash
casablanca test
```

---

## Examples

Below are some practical examples of Casablanca usage:

### Record Messages from Multiple Queues

Record messages from multiple queues in RabbitMQ and save them into separate files:

```bash
casablanca record --queue queue1 --output queue1.log
casablanca record --queue queue2 --output queue2.log
```

### Replay Messages with Delays

Replay recorded messages into RabbitMQ at a controlled pace by adding a delay between each message:

```bash
casablanca replay --input messages.log --queue test-queue --delay 1
```

This replays the messages in `messages.log` to `test-queue`, introducing a 1-second delay between each message.

### Load Testing with Recorded Data

Use recorded data to simulate load testing by replaying messages at high speeds:

```bash
casablanca replay --input large-dataset.log --queue stress-test-queue --parallel-workers 10
```

This replays large datasets using 10 workers to `stress-test-queue` for performance testing.

---

## Contribution

We welcome contributions to improve Casablanca! Here's how you can get involved:

1. **Report Issues**: Found a bug? Have suggestions? Open an issue on GitHub.
2. **Submit Pull Requests**: Fork the repository, make your changes, and submit a PR.
3. **Improve Documentation**: Help expand or enhance the documentation.
4. **Add Tests**: Write new tests (both unit and functional) to improve code coverage and reliability.

---

## License

Casablanca is licensed under [Your Preferred Open Source License]. See the `LICENSE` file in the repository for further details.

---

## Feedback

We’d love to hear your feedback! If you encounter any issues, have suggestions, or want to request a feature, feel free to open an issue or contact the maintainers. Happy coding with Casablanca! 🎉
