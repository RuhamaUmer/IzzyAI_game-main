Here's the updated README with additional instructions for accessing the next games:

---

# Izzy AI Games

## Description

Izzy AI Games is a collection of interactive games designed to provide therapeutic exercises for various disorders. This repository contains the source code and instructions to set up and run the application.

## Getting Started

### Prerequisites

- Python 3.9 or greater
- pip (Python package installer)

### Installation

1. **Clone the repository**

   Open your terminal and run:

   ```bash
   git clone <repository_url>
   ```

2. **Change to the repository directory**

   Navigate to the cloned repository:

   ```bash
   cd <game-directory>
   ```

3. **Install the required packages**

   Install the dependencies listed in the `requirements.txt` file:

   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**

   Start the application by running:

   ```bash
   python app.py
   ```

5. **Open the first game**

   Open your web browser and go to the following URL:

   ```
   http://127.0.0.1:5001/start_blow_game/<int:user_id>/3
   ```

   Replace `<int:user_id>` with the appropriate integer value for the user.

6. **Open the Second game**

   Open your web browser and go to the following URL:

   ```
   http://127.0.0.1:5001/start_sounds_game/<int:user_id>/3
   ```

   Replace `<int:user_id>` with the appropriate integer value for the user.

7. **Open the third game**

   To start the Transport Game, go to:

   ```
   http://127.0.0.1:5001/start_animal_game/<int:user-id>/3
   ```

   Replace `<int:user_id>` with the appropriate integer value for the user.

8. **Open the fourth game**

   To start the Transport Game, go to:

   ```
   http://127.0.0.1:5001/start_transport_game/<int:user-id>/3
   ```

   Replace `<int:user_id>` with the appropriate integer value for the user.

9. **Open the fifth game**

   To start the Food Game, go to:

   ```
   http://127.0.0.1:5001/start_food_game/<int:user-id>/3
   ```

   Replace `<int:user_id>` with the appropriate integer value for the user.

---

Feel free to replace `<repository_url>` and `<game-directory>` with the actual repository URL and directory name.
