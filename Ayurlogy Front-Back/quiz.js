  const questions = [
    {
      q: "What best describes your body build?",
      options: ["Thin, light, lean", "Medium, muscular, well-shaped", "Broad, strong, heavier build"],
      dosha: ["V", "P", "K"]
    },
    {
      q: "How is your appetite usually?",
      options: ["Irregular, sometimes hungry", "Strong and sharp hunger", "Slow but steady appetite"],
      dosha: ["V", "P", "K"]
    },
    {
      q: "How is your skin type?",
      options: ["Dry, rough, thin", "Warm, oily, acne-prone", "Soft, thick, oily"],
      dosha: ["V", "P", "K"]
    },
    {
      q: "How do you usually feel in cold weather?",
      options: ["Very cold and uncomfortable", "Neutral", "Comfortable"],
      dosha: ["V", "P", "K"]
    },
    {
      q: "How is your energy during the day?",
      options: ["High bursts but tire quickly", "Strong, intense energy", "Slow start but long stamina"],
      dosha: ["V", "P", "K"]
    },
    {
      q: "How is your sleep pattern?",
      options: ["Light sleeper", "Moderate and sound", "Deep and long"],
      dosha: ["V", "P", "K"]
    },
    {
      q: "How do you respond to stress?",
      options: ["Anxious and worried", "Angry and frustrated", "Withdraw and quiet"],
      dosha: ["V", "P", "K"]
    },
    {
      q: "How is your digestion after meals?",
      options: ["Gas, bloating", "Acidity or burning", "Heaviness and sleepiness"],
      dosha: ["V", "P", "K"]
    },
    {
      q: "How would you describe your personality?",
      options: ["Creative and enthusiastic", "Ambitious and focused", "Calm and caring"],
      dosha: ["V", "P", "K"]
    },
    {
      q: "How do you usually speak?",
      options: ["Fast and talkative", "Clear and direct", "Slow and steady"],
      dosha: ["V", "P", "K"]
    },
    {
      q: "How do you usually walk or move?",
      options: ["Quick and restless", "Purposeful and strong", "Slow and relaxed"],
      dosha: ["V", "P", "K"]
    },
    {
      q: "Which climate do you prefer most?",
      options: ["Warm and humid", "Cool and airy", "Warm and dry"],
      dosha: ["V", "P", "K"]
    },
    {
      q: "How do you make decisions?",
      options: ["Quickly but change later", "Firm and confident", "Slow and careful"],
      dosha: ["V", "P", "K"]
    },
    {
      q: "How is your memory style?",
      options: ["Fast learning, fast forgetting", "Sharp and focused", "Slow learning, strong memory"],
      dosha: ["V", "P", "K"]
    },
    {
      q: "What foods do you crave most?",
      options: ["Warm soups and snacks", "Spicy and sour foods", "Sweet and creamy foods"],
      dosha: ["V", "P", "K"]
    }
  ];

  let current = 0;
  let answers = Array(questions.length).fill(null);

  function startQuiz() {
    document.querySelector(".hero").style.display = "none";
    document.getElementById("quizSection").style.display = "block";
    loadQuestion();
  }

  function loadQuestion() {
    const q = questions[current];
    document.getElementById("progress").innerHTML = `Question ${current + 1} of ${questions.length}`;
    document.getElementById("questionText").innerText = q.q;
    const box = document.getElementById("optionsBox");
    box.innerHTML = "";

    q.options.forEach((opt, i) => {
      const label = document.createElement("label");
      label.innerHTML = `
        <input type="radio" name="option" value="${i}" ${answers[current] === i ? "checked" : ""}>
        <span>${String.fromCharCode(65+i)}. ${opt}</span>
      `;
      label.querySelector("input").addEventListener("change", () => {
        answers[current] = i;
      });
      box.appendChild(label);
    });
  }

  function nextQuestion() {
    if (answers[current] === null) {
      toastWarning("Please select an option before continuing.");
      return;
    }
    if (current < questions.length - 1) {
      current++;
      loadQuestion();
    } else {
      showResult();
    }
  }

  function prevQuestion() {
    if (current > 0) {
      current--;
      loadQuestion();
    }
  }

  function showResult() {
    let v = 0, p = 0, k = 0;
    answers.forEach((ans, i) => {
      const d = questions[i].dosha[ans];
      if (d === "V") 
        v++;
      if (d === "P") 
        p++;
      if (d === "K") 
        k++;
    });

    let result = "";
    let description = "";

    if (v > p && v > k) {
      result = "Vata Dominant";
      description = "You are energetic, creative, and quick-thinking. You benefit most from warm foods, regular routines, and grounding activities like meditation and gentle yoga.";
    } else if (p > v && p > k) {
      result = "Pitta Dominant";
      description = "You are intelligent, ambitious, and focused. Cooling foods, calm environments, and stress management help keep you balanced.";
    } else if (k > v && k > p) {
      result = "Kapha Dominant";
      description = "You are calm, nurturing, and stable. You thrive with light foods, regular movement, and stimulating activities.";
    } else if (v === p && v > k) {
      result = "Vata–Pitta Type";
      description = "You combine creativity with leadership. Balance warmth and cooling, rest and activity, to stay in harmony.";
    } else if (p === k && p > v) {
      result = "Pitta–Kapha Type";
      description = "You are driven yet steady. Balance intensity with relaxation and lightness.";
    } else if (v === k && v > p) {
      result = "Vata–Kapha Type";
      description = "You combine creativity with stability. Maintain warmth, movement, and consistency.";
    } else {
      result = "Tridoshic (Balanced Type)";
      description = "You have a balanced constitution of all three doshas. Maintain a balanced lifestyle to preserve harmony.";
    }

    document.getElementById("quizBox").style.display = "none";
    document.getElementById("resultBox").style.display = "block";
    document.getElementById("resultText").innerText = result;
    document.getElementById("resultDescription").innerText = description;
  }

  function restartQuiz() {
    current = 0;
    answers = Array(questions.length).fill(null);
    document.getElementById("quizBox").style.display = "block";
    document.getElementById("resultBox").style.display = "none";
    loadQuestion();
  }