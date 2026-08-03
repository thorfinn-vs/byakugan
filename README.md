# BYAKUGAN 
**Automated REST API Method & Schema Introspection Workbench**

[![License: MIT](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/Backend-Flask-green.svg)](https://flask.palletsprojects.com/)
[![UI](https://img.shields.io/badge/Frontend-React-cyan.svg)](https://react.dev/)

**Byakugan** is an open-source security research tool designed for Application Security (AppSec) engineers, penetration testers, and bug bounty hunters. It automates HTTP verb discovery (`OPTIONS`, `GET`, `POST`, `PUT`, `PATCH`, `DELETE`), validation-error schema inference, mass-assignment flag detection, and JSON payload synthesis for REST API endpoints.

---

##  Key Features

- **Error-Driven Schema Reconstruction:** Instead of relying on blind wordlist fuzzing, Byakugan parses `400` / `422` validation error outputs from modern frameworks (FastAPI/Pydantic, Django REST, Zod, and Jackson) to automatically infer required request body fields and data types.
- **GET Response Baseline Mapping:** Derives object properties directly from baseline `GET` responses.
- **Mass Assignment Candidate Spotter:** Automatically highlights privilege-sensitive fields (`role`, `is_admin`, `verified`, `tier`, `balance`) for over-posting tests.
- **Safety-Gated Destructive Operations:** Prevents accidental data loss by prompting user confirmation before executing `DELETE` probes.
- **Multi-Format Payload Exporter:** Instantly generates ready-to-use **JSON Bodies**, **cURL commands**, and **Burp Suite Repeater HTTP requests**.

---

##  System Architecture

```
                       +-------------------------------+
                       |  Byakugan React Web Dashboard |
                       +---------------+---------------+
                                       |
                                       | POST /api/probe
                                       v
                       +---------------+---------------+
                       |    Flask Backend Engine       |
                       +---------------+---------------+
                                       |
                   +-------------------+-------------------+
                   |                   |                   |
                   v                   v                   v
            OPTIONS / GET        POST/PUT/PATCH          DELETE
           (Baseline Schema)    (Empty Body Fuzz)   (Safety Modal)
                   |                   |                   |
                   +-------------------+-------------------+
                                       |
                                       v
                       +---------------+---------------+
                       | Framework Validation Parsers  |
                       |  (Pydantic/Django/Zod/Spring)  |
                       +---------------+---------------+
                                       |
                                       v
                       +---------------+---------------+
                       | Field Matrix & Payload Synth  |
                       +-------------------------------+
```

---

##  Getting Started

### Prerequisites
- Python 3.9 or higher

### Installation & Execution

1. **Clone the repository:**
   ```bash
   git clone https://github.com/thorfinn-vs/byakugan.git
   cd byakugan
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Start the application:**
   ```bash
   python app.py
   ```

4. **Access the Web Dashboard:**
   Open `http://localhost:5000` in your web browser.

---

##  Local Test Lab (Included)

To test Byakugan locally without targeting external systems, run the included mock target server:

```bash
python lab_server.py
```
- **Target URL:** `http://localhost:5001/api/v1/users/123`
- Enter this URL into Byakugan to visualize baseline fields, 422 Pydantic error parsing, and mass-assignment flags.

---


##  Contributing

Contributions, framework parser updates, and feature requests are welcome! Feel free to open an issue or submit a pull request.
