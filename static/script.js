// ==========================================
// AI Study Buddy - Complete Frontend Logic
// ==========================================
// This file handles all user interactions:
//   1. Tab navigation
//   2. PDF upload with drag & drop
//   3. Chat with AI
//   4. Summary generation
//   5. Quiz generation and evaluation
//   6. Flashcard generation and flip

// ------------------------------------------
// GLOBAL STATE
// ------------------------------------------

// Tracks whether a PDF has been uploaded
let pdfUploaded = false;

// Stores the selected file before upload
let selectedFile = null;

// Stores generated quiz data for evaluation
let currentQuiz = [];

// Tracks how many quiz questions answered
let answeredCount = 0;

// Tracks correct answers in current quiz
let correctCount = 0;


// ------------------------------------------
// 1. TAB NAVIGATION
// ------------------------------------------

/**
 * Show a specific section and highlight its tab button.
 * Called when user clicks any nav tab button.
 *
 * @param {string} sectionId - ID of the section to show
 */
function showSection(sectionId) {
  // Hide all sections
  document.querySelectorAll('.section').forEach(sec => {
    sec.classList.remove('active');
  });

  // Remove active state from all tab buttons
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.classList.remove('active');
  });

  // Show the selected section
  document.getElementById(sectionId).classList.add('active');

  // Highlight the clicked tab button
  // Match button by its onclick attribute content
  document.querySelectorAll('.tab-btn').forEach(btn => {
    if (btn.getAttribute('onclick').includes(sectionId)) {
      btn.classList.add('active');
    }
  });
}


// ------------------------------------------
// 2. PDF UPLOAD — FILE SELECTION
// ------------------------------------------

/**
 * Handle file selected via the file input click.
 * Shows file name and the upload button.
 *
 * @param {Event} event - The file input change event
 */
function handleFileSelect(event) {
  const file = event.target.files[0];
  if (file) setSelectedFile(file);
}

/**
 * Handle file dropped onto the upload box.
 *
 * @param {DragEvent} event - The drop event
 */
function handleDrop(event) {
  event.preventDefault();
  document.getElementById('uploadBox').classList.remove('drag-over');

  const file = event.dataTransfer.files[0];
  if (!file) return;

  // Only allow PDF files
  if (file.type !== 'application/pdf') {
    showUploadError('Only PDF files are allowed.');
    return;
  }

  setSelectedFile(file);
}

/**
 * Add visual highlight when file is dragged over the box.
 *
 * @param {DragEvent} event
 */
function handleDragOver(event) {
  event.preventDefault();
  document.getElementById('uploadBox').classList.add('drag-over');
}

/**
 * Remove visual highlight when drag leaves the box.
 *
 * @param {DragEvent} event
 */
function handleDragLeave(event) {
  document.getElementById('uploadBox').classList.remove('drag-over');
}

/**
 * Store the selected file and update the UI.
 * Shows the file name row and the upload button.
 *
 * @param {File} file - The selected PDF file
 */
function setSelectedFile(file) {
  selectedFile = file;

  // Show file info row
  document.getElementById('fileName').textContent = file.name;
  document.getElementById('fileInfo').style.display = 'flex';

  // Show upload button
  document.getElementById('uploadBtn').style.display = 'inline-flex';

  // Hide any previous status messages
  hideUploadMessages();
}

/**
 * Clear the selected file and reset the upload UI.
 */
function clearFile() {
  selectedFile = null;
  document.getElementById('fileInput').value = '';
  document.getElementById('fileInfo').style.display = 'none';
  document.getElementById('uploadBtn').style.display = 'none';
  hideUploadMessages();
}


// ------------------------------------------
// 3. PDF UPLOAD — SEND TO BACKEND
// ------------------------------------------

/**
 * Upload the selected PDF to the Flask backend.
 * On success: builds the vector store and marks PDF as ready.
 * On failure: shows an error message.
 */
async function uploadPDF() {
  if (!selectedFile) {
    showUploadError('Please select a PDF file first.');
    return;
  }

  // Build form data with the file
  const formData = new FormData();
  formData.append('file', selectedFile);

  // Show loader, hide button
  showElement('uploadLoader');
  document.getElementById('uploadBtn').disabled = true;
  hideUploadMessages();

  try {
    const response = await fetch('/upload', {
      method: 'POST',
      body: formData
    });

    const data = await response.json();

    if (response.ok && data.success) {
      // Mark PDF as uploaded
      pdfUploaded = true;

      // Show success message
      showUploadSuccess(
        `✅ ${data.message} ` +
        `(${data.characters?.toLocaleString() || 0} characters extracted)`
      );

      // Reset file selection UI
      clearFile();

    } else {
      showUploadError(data.error || 'Upload failed. Please try again.');
    }

  } catch (error) {
    showUploadError('Network error. Is the Flask server running?');
    console.error('Upload error:', error);

  } finally {
    // Always hide loader and re-enable button
    hideElement('uploadLoader');
    document.getElementById('uploadBtn').disabled = false;
  }
}


// ------------------------------------------
// 4. CHAT — SEND MESSAGE
// ------------------------------------------

/**
 * Send the user's question to the backend and display the answer.
 * Uses the RAG pipeline: FAISS search → IBM Granite → answer.
 */
async function sendMessage() {
  const input = document.getElementById('chatInput');
  const question = input.value.trim();

  // Validate input
  if (!question) return;

  // Clear input field
  input.value = '';

  // Add user message bubble to chat window
  addChatMessage(question, 'user');

  // Show typing loader
  showElement('chatLoader');

  try {
    const response = await fetch('/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question })
    });

    const data = await response.json();

    if (response.ok && data.success) {
      // Add AI answer bubble
      addChatMessage(data.answer, 'bot');
    } else {
      addChatMessage(
        '⚠️ ' + (data.error || 'Something went wrong. Please try again.'),
        'bot'
      );
    }

  } catch (error) {
    addChatMessage('⚠️ Network error. Is the Flask server running?', 'bot');
    console.error('Chat error:', error);

  } finally {
    hideElement('chatLoader');
  }
}

/**
 * Add a chat message bubble to the chat window.
 * Automatically scrolls to the latest message.
 *
 * @param {string} text    - The message text
 * @param {string} sender  - 'user' or 'bot'
 */
function addChatMessage(text, sender) {
  const chatWindow = document.getElementById('chatWindow');

  // Create message container
  const messageDiv = document.createElement('div');
  messageDiv.className = `chat-message ${sender}`;

  // Avatar emoji
  const avatar = document.createElement('div');
  avatar.className = 'chat-avatar';
  avatar.textContent = sender === 'bot' ? '🤖' : '👤';

  // Message bubble
  const bubble = document.createElement('div');
  bubble.className = 'chat-bubble';
  bubble.textContent = text;

  messageDiv.appendChild(avatar);
  messageDiv.appendChild(bubble);
  chatWindow.appendChild(messageDiv);

  // Scroll to latest message
  chatWindow.scrollTop = chatWindow.scrollHeight;
}


// ------------------------------------------
// 5. SUMMARY GENERATION
// ------------------------------------------

/**
 * Request a summary of the uploaded notes from the backend.
 * Displays the result in the output box.
 */
async function generateSummary() {
  // Show loader, hide previous output
  showElement('summaryLoader');
  hideElement('summaryOutput');
  hideElement('summaryError');

  try {
    const response = await fetch('/summary', { method: 'POST' });
    const data = await response.json();

    if (response.ok && data.success) {
      // Display the summary
      document.getElementById('summaryText').textContent = data.summary;
      showElement('summaryOutput');
    } else {
      showError('summaryError', data.error || 'Summary generation failed.');
    }

  } catch (error) {
    showError('summaryError', 'Network error. Is the Flask server running?');
    console.error('Summary error:', error);

  } finally {
    hideElement('summaryLoader');
  }
}


// ------------------------------------------
// 6. QUIZ GENERATION & EVALUATION
// ------------------------------------------

/**
 * Request quiz questions from the backend.
 * Renders each question with clickable A/B/C/D options.
 */
async function generateQuiz() {
  // Reset quiz state
  currentQuiz = [];
  answeredCount = 0;
  correctCount = 0;

  // Show loader, clear previous quiz
  showElement('quizLoader');
  hideElement('scoreBox');
  hideElement('quizError');

  const quizOutput = document.getElementById('quizOutput');
  quizOutput.innerHTML = '';
  quizOutput.style.display = 'none';

  try {
    const response = await fetch('/quiz', { method: 'POST' });
    const data = await response.json();

    if (response.ok && data.success) {
      currentQuiz = data.quiz;
      renderQuiz(data.quiz);
    } else {
      showError('quizError', data.error || 'Quiz generation failed.');
    }

  } catch (error) {
    showError('quizError', 'Network error. Is the Flask server running?');
    console.error('Quiz error:', error);

  } finally {
    hideElement('quizLoader');
  }
}

/**
 * Render quiz questions and options into the DOM.
 *
 * @param {Array} questions - Array of question objects from the backend
 */
function renderQuiz(questions) {
  const quizOutput = document.getElementById('quizOutput');
  quizOutput.innerHTML = '';

  questions.forEach((q, index) => {
    // Question card
    const card = document.createElement('div');
    card.className = 'quiz-question-card';
    card.id = `question-${index}`;

    // Question number label
    const numberLabel = document.createElement('div');
    numberLabel.className = 'quiz-question-number';
    numberLabel.textContent = `Question ${index + 1} of ${questions.length}`;

    // Question text
    const questionText = document.createElement('div');
    questionText.className = 'quiz-question-text';
    questionText.textContent = q.question;

    // Options container
    const optionsDiv = document.createElement('div');
    optionsDiv.className = 'quiz-options';

    // Create A, B, C, D option buttons
    Object.entries(q.options).forEach(([key, value]) => {
      const optionBtn = document.createElement('button');
      optionBtn.className = 'quiz-option';
      optionBtn.id = `option-${index}-${key}`;

      // onclick: evaluate this answer
      optionBtn.onclick = () => evaluateAnswer(index, key, q.answer);

      // Option label badge (A / B / C / D)
      const label = document.createElement('span');
      label.className = 'option-label';
      label.textContent = key;

      // Option text
      const text = document.createElement('span');
      text.textContent = value;

      optionBtn.appendChild(label);
      optionBtn.appendChild(text);
      optionsDiv.appendChild(optionBtn);
    });

    // Assemble card
    card.appendChild(numberLabel);
    card.appendChild(questionText);
    card.appendChild(optionsDiv);
    quizOutput.appendChild(card);
  });

  quizOutput.style.display = 'block';
}

/**
 * Evaluate a selected quiz answer.
 * Colors the selected option green (correct) or red (wrong).
 * Disables all options after answering.
 * Shows score when all questions are answered.
 *
 * @param {number} questionIndex  - Index of the question (0-based)
 * @param {string} selectedKey    - The option selected by user (A/B/C/D)
 * @param {string} correctKey     - The correct answer key (A/B/C/D)
 */
function evaluateAnswer(questionIndex, selectedKey, correctKey) {
  const isCorrect = selectedKey === correctKey;

  // Update counters
  answeredCount++;
  if (isCorrect) correctCount++;

  // Disable all options for this question (prevent re-answering)
  ['A', 'B', 'C', 'D'].forEach(key => {
    const btn = document.getElementById(`option-${questionIndex}-${key}`);
    if (!btn) return;

    btn.disabled = true;

    // Highlight correct answer green
    if (key === correctKey) {
      btn.classList.add('correct');
    }

    // Highlight wrong selection red
    if (key === selectedKey && !isCorrect) {
      btn.classList.add('wrong');
    }
  });

  // Check if all questions answered → show score
  if (answeredCount === currentQuiz.length) {
    showScore();
  }
}

/**
 * Display the final quiz score after all questions are answered.
 */
function showScore() {
  const total = currentQuiz.length;
  const percentage = Math.round((correctCount / total) * 100);

  // Choose emoji based on score
  let emoji = '😔';
  if (percentage >= 80) emoji = '🎉';
  else if (percentage >= 60) emoji = '👍';
  else if (percentage >= 40) emoji = '📚';

  document.getElementById('scoreText').textContent =
    `${correctCount} / ${total} (${percentage}%) ${emoji}`;

  showElement('scoreBox');

  // Scroll to score box
  document.getElementById('scoreBox').scrollIntoView({ behavior: 'smooth' });
}


// ------------------------------------------
// 7. FLASHCARD GENERATION
// ------------------------------------------

/**
 * Request flashcards from the backend.
 * Renders them as flippable cards in a grid.
 */
async function generateFlashcards() {
  // Show loader, clear previous cards
  showElement('flashcardsLoader');
  hideElement('flashcardsError');

  const grid = document.getElementById('flashcardsOutput');
  grid.innerHTML = '';

  try {
    const response = await fetch('/flashcards', { method: 'POST' });
    const data = await response.json();

    if (response.ok && data.success) {
      renderFlashcards(data.flashcards);
    } else {
      showError('flashcardsError', data.error || 'Flashcard generation failed.');
    }

  } catch (error) {
    showError('flashcardsError', 'Network error. Is the Flask server running?');
    console.error('Flashcard error:', error);

  } finally {
    hideElement('flashcardsLoader');
  }
}

/**
 * Render flashcards as flippable cards in the grid.
 *
 * @param {Array} flashcards - Array of {question, answer} objects
 */
function renderFlashcards(flashcards) {
  const grid = document.getElementById('flashcardsOutput');
  grid.innerHTML = '';

  flashcards.forEach((card, index) => {
    // Outer flip container
    const flipCard = document.createElement('div');
    flipCard.className = 'flashcard';
    flipCard.id = `flashcard-${index}`;
    flipCard.onclick = () => flipCard.classList.toggle('flipped');

    // Inner rotating element
    const inner = document.createElement('div');
    inner.className = 'flashcard-inner';

    // --- Front face (Question) ---
    const front = document.createElement('div');
    front.className = 'flashcard-front';

    const frontLabel = document.createElement('div');
    frontLabel.className = 'card-label';
    frontLabel.textContent = '❓ Question';

    const frontText = document.createElement('div');
    frontText.className = 'card-text';
    frontText.textContent = card.question;

    const flipHint = document.createElement('div');
    flipHint.className = 'flip-hint';
    flipHint.textContent = 'Click to reveal answer';

    front.appendChild(frontLabel);
    front.appendChild(frontText);
    front.appendChild(flipHint);

    // --- Back face (Answer) ---
    const back = document.createElement('div');
    back.className = 'flashcard-back';

    const backLabel = document.createElement('div');
    backLabel.className = 'card-label';
    backLabel.textContent = '✅ Answer';

    const backText = document.createElement('div');
    backText.className = 'card-text';
    backText.textContent = card.answer;

    back.appendChild(backLabel);
    back.appendChild(backText);

    // Assemble the card
    inner.appendChild(front);
    inner.appendChild(back);
    flipCard.appendChild(inner);
    grid.appendChild(flipCard);
  });
}


// ------------------------------------------
// 8. UTILITY FUNCTIONS
// ------------------------------------------

/**
 * Copy text content of an element to clipboard.
 *
 * @param {string} elementId - ID of the element to copy from
 */
function copyText(elementId) {
  const text = document.getElementById(elementId)?.textContent;
  if (!text) return;

  navigator.clipboard.writeText(text)
    .then(() => alert('✅ Copied to clipboard!'))
    .catch(() => alert('Could not copy. Please copy manually.'));
}

/**
 * Show a DOM element (removes display:none).
 *
 * @param {string} id - Element ID
 */
function showElement(id) {
  const el = document.getElementById(id);
  if (el) el.style.display = '';
}

/**
 * Hide a DOM element (sets display:none).
 *
 * @param {string} id - Element ID
 */
function hideElement(id) {
  const el = document.getElementById(id);
  if (el) el.style.display = 'none';
}

/**
 * Show a success message in the upload section.
 *
 * @param {string} message - Success message text
 */
function showUploadSuccess(message) {
  const el = document.getElementById('uploadSuccess');
  el.textContent = message;
  el.style.display = 'block';
}

/**
 * Show an error message in the upload section.
 *
 * @param {string} message - Error message text
 */
function showUploadError(message) {
  const el = document.getElementById('uploadError');
  el.textContent = '⚠️ ' + message;
  el.style.display = 'block';
}

/**
 * Hide all upload status messages.
 */
function hideUploadMessages() {
  hideElement('uploadSuccess');
  hideElement('uploadError');
}

/**
 * Show an error message in any section.
 *
 * @param {string} elementId - ID of the error element
 * @param {string} message   - Error message text
 */
function showError(elementId, message) {
  const el = document.getElementById(elementId);
  if (el) {
    el.textContent = '⚠️ ' + message;
    el.style.display = 'block';
  }
}