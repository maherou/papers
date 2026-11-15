/*
 * Article Quiz player. Loads a question file named by ?quiz=<path-or-url>
 * and runs a Take the Challenge quiz. No build step, no dependencies.
 * Once the page and quiz file have loaded, it makes no further network calls.
 */
(function () {
  "use strict";

  var PLAYER_VERSION = "0.1.3";
  var SUPPORTED_SCHEMA_VERSIONS = [1];

  var app = document.getElementById("app");
  var scoreEl = document.getElementById("score");
  document.getElementById("player-version").textContent = "Player v" + PLAYER_VERSION;

  var quiz = null;
  var state = null;

  // About panel. It only opens and closes a <dialog>; quiz state is untouched.
  // Escape closes it natively; a click on the backdrop lands on the dialog itself.
  var about = document.getElementById("about");
  document.getElementById("about-open").addEventListener("click", function () { about.showModal(); });
  document.getElementById("about-close").addEventListener("click", function () { about.close(); });
  about.addEventListener("click", function (event) { if (event.target === about) about.close(); });

  // ---- helpers -----------------------------------------------------------

  function el(tag, attrs, children) {
    var node = document.createElement(tag);
    if (attrs) {
      Object.keys(attrs).forEach(function (key) {
        var value = attrs[key];
        if (value === null || value === undefined || value === false) return;
        if (key === "text") node.textContent = value;
        else if (key === "class") node.className = value;
        else if (key.slice(0, 2) === "on") node.addEventListener(key.slice(2), value);
        else node.setAttribute(key, value === true ? "" : value);
      });
    }
    (children || []).forEach(function (child) {
      if (child === null || child === undefined || child === false) return;
      node.appendChild(typeof child === "string" ? document.createTextNode(child) : child);
    });
    return node;
  }

  // Only http(s) links are rendered; anything else in the file is ignored.
  function safeUrl(value) {
    if (typeof value !== "string" || !value) return null;
    try {
      var url = new URL(value, location.href);
      return url.protocol === "https:" || url.protocol === "http:" ? url.href : null;
    } catch (e) {
      return null;
    }
  }

  function link(href, text) {
    return el("a", { href: href, target: "_blank", rel: "noopener" }, [text]);
  }

  function fmt(n) {
    return String(Math.round(n * 100) / 100);
  }

  function show(nodes, focusTarget) {
    app.replaceChildren.apply(app, nodes);
    window.scrollTo(0, 0);
    (focusTarget || app).focus({ preventScroll: true });
  }

  function showError(message) {
    scoreEl.hidden = true;
    var heading = el("h1", { tabindex: "-1", text: "This quiz can't be shown" });
    show([heading, el("div", { class: "error", role: "alert" }, [el("p", { text: message })])], heading);
  }

  function shareUrl() {
    return location.origin + location.pathname + location.search;
  }

  function updateScore() {
    if (!state) return;
    scoreEl.hidden = false;
    scoreEl.textContent = "Score " + fmt(state.score) + "/" + state.answered;
  }

  // ---- loading and checking ----------------------------------------------

  function checkQuiz(data) {
    if (!data || typeof data !== "object") return "The quiz file is not a JSON object.";
    if (SUPPORTED_SCHEMA_VERSIONS.indexOf(data.schema_version) === -1) {
      return "This quiz file uses schema version " + JSON.stringify(data.schema_version) +
        ", but this player (v" + PLAYER_VERSION + ") supports only version " +
        SUPPORTED_SCHEMA_VERSIONS.join(", ") + ". The player may need updating.";
    }
    if (!data.paper || typeof data.paper.title !== "string") return "The quiz file has no paper title.";
    if (!Array.isArray(data.questions) || data.questions.length === 0) return "The quiz file has no questions.";
    for (var i = 0; i < data.questions.length; i++) {
      var q = data.questions[i];
      var label = "Question " + (i + 1);
      if (!q || (q.type !== "single" && q.type !== "multi")) return label + " has an unknown type.";
      if (typeof q.prompt !== "string" || !Array.isArray(q.choices) || q.choices.length < 2) {
        return label + " is missing its prompt or choices.";
      }
      var correct = q.choices.filter(function (c) { return c && c.correct === true; }).length;
      if (q.type === "single" && correct !== 1) return label + " must have exactly one correct choice.";
      if (q.type === "multi" && correct < 2) return label + " must have at least two correct choices.";
    }
    return null;
  }

  function load() {
    var param = new URLSearchParams(location.search).get("quiz");
    if (!param) {
      showError("No quiz was named. Open this page as player.html?quiz=<path-or-url-to-quiz.json>.");
      return;
    }
    var url;
    try {
      url = new URL(param, location.href);
    } catch (e) {
      showError("The quiz address \"" + param + "\" is not a valid path or URL.");
      return;
    }
    fetch(url.href)
      .then(function (res) {
        if (!res.ok) throw new Error("the server answered " + res.status + " " + res.statusText);
        return res.json().catch(function () { throw new Error("the file is not valid JSON"); });
      })
      .then(function (data) {
        var problem = checkQuiz(data);
        if (problem) { showError(problem); return; }
        quiz = data;
        document.title = "Take the Challenge: " + quiz.paper.title;
        renderIntro();
      })
      .catch(function (err) {
        var hint = location.protocol === "file:" ?
          " Browsers block loading files from a file:// page; serve the folder over HTTP instead." : "";
        showError("Could not load the quiz from " + url.href + ": " + err.message + "." + hint);
      });
  }

  // ---- screens -----------------------------------------------------------

  function paperLinks() {
    var p = quiz.paper;
    var items = [];
    var doi = typeof p.doi === "string" && /^10\.\S+\/\S+$/.test(p.doi) ? p.doi : null;
    if (doi) items.push(el("li", null, ["DOI: ", link("https://doi.org/" + doi, doi)]));
    var pdf = safeUrl(p.pdf_url);
    if (pdf) items.push(el("li", null, [link(pdf, "Read the paper (PDF)")]));
    var video = safeUrl(p.video_url);
    if (video) items.push(el("li", null, [link(video, "Watch the pitch video")]));
    return items.length ? el("ul", { class: "meta" }, items) : null;
  }

  function maxPoints() {
    return quiz.questions.length;
  }

  function renderIntro() {
    state = null;
    scoreEl.hidden = true;
    var p = quiz.paper;
    var authors = Array.isArray(p.authors) ? p.authors.filter(Boolean).join(", ") : "";
    var n = quiz.questions.length;
    var heading = el("h1", { tabindex: "-1", text: p.title });
    show([
      el("p", { class: "progress", text: "Quiz" }),
      heading,
      authors ? el("p", { class: "authors", text: authors }) : null,
      paperLinks(),
      el("p", { class: "lede", text: n + " question" + (n === 1 ? "" : "s") +
        ". One attempt each. Select-all questions give partial credit." }),
      el("div", { class: "actions" }, [el("button", { class: "btn", type: "button", onclick: start, text: "Start" })])
    ], heading);
  }

  function start() {
    state = { index: 0, score: 0, answered: 0 };
    updateScore();
    renderQuestion();
  }

  function renderQuestion() {
    var q = quiz.questions[state.index];
    var multi = q.type === "multi";
    var selected = {};
    var buttons = [];
    var submit = null;

    var heading = el("h2", { tabindex: "-1", text: q.prompt });
    var list = el("ul", { class: "choices" + (multi ? " multi" : ""), role: "list" });

    q.choices.forEach(function (choice, i) {
      var btn = el("button", {
        class: "choice",
        type: "button",
        "aria-pressed": multi ? "false" : null,
        onclick: function () {
          if (multi) {
            selected[i] = !selected[i];
            btn.setAttribute("aria-pressed", selected[i] ? "true" : "false");
            submit.disabled = !Object.keys(selected).some(function (k) { return selected[k]; });
          } else {
            selected[i] = true;
            grade();
          }
        }
      }, [
        el("span", { class: "mark", "aria-hidden": "true", text: String.fromCharCode(65 + i) }),
        el("span", { class: "text", text: choice.text })
      ]);
      buttons.push(btn);
      list.appendChild(el("li", null, [btn]));
    });

    var actions = el("div", { class: "actions" });
    if (multi) {
      submit = el("button", { class: "btn", type: "button", disabled: true, onclick: grade, text: "Submit" });
      actions.appendChild(submit);
    }

    var feedbackSlot = el("div", { "aria-live": "polite" });

    show([
      el("p", { class: "progress", text: "Question " + (state.index + 1) + " of " + quiz.questions.length }),
      heading,
      el("p", { class: "hint", text: multi ? "Select all that apply, then press Submit." : "Tap one answer." }),
      list,
      feedbackSlot,
      actions
    ], heading);

    function grade() {
      var nCorrect = 0, hits = 0, misses = 0;
      q.choices.forEach(function (choice, i) {
        if (choice.correct) nCorrect++;
        if (selected[i]) { if (choice.correct) hits++; else misses++; }
      });
      var points = multi ? Math.max(0, (hits - misses) / nCorrect) : (hits === 1 ? 1 : 0);
      state.score += points;
      state.answered += 1;
      updateScore();

      buttons.forEach(function (btn, i) {
        var choice = q.choices[i];
        btn.disabled = true;
        btn.removeAttribute("aria-pressed");
        var tag = null;
        if (choice.correct && selected[i]) { btn.classList.add("is-correct"); tag = "Correct"; }
        else if (choice.correct) { btn.classList.add(multi ? "is-missed" : "is-correct"); tag = multi ? "Missed: correct answer" : "Correct answer"; }
        else if (selected[i]) { btn.classList.add("is-wrong"); tag = "Your answer: incorrect"; }
        if (tag) btn.querySelector(".text").appendChild(el("span", { class: "tag", text: tag }));
      });

      var verdictText, verdictClass;
      if (points === 1) { verdictText = "Correct! +1"; verdictClass = "good"; }
      else if (points > 0) { verdictText = "Partly correct: +" + fmt(points); verdictClass = "partial"; }
      else { verdictText = "Not quite: +0"; verdictClass = "bad"; }

      var feedback = el("div", { class: "feedback" }, [
        el("p", { class: "verdict " + verdictClass, text: verdictText }),
        q.explanation ? el("p", { class: "explanation", text: q.explanation }) : null,
        q.quote ? el("blockquote", null, [el("p", { text: q.quote })]) : null,
        q.location ? el("p", { class: "location", text: "— " + q.location }) : null
      ]);
      feedbackSlot.appendChild(feedback);
      // On a phone the feedback usually lands below the fold; bring it up.
      if (feedback.getBoundingClientRect().top > window.innerHeight * 0.6) {
        feedback.scrollIntoView({ behavior: "smooth", block: "start" });
      }

      var last = state.index === quiz.questions.length - 1;
      var next = el("button", {
        class: "btn", type: "button", text: last ? "See your score" : "Next",
        onclick: function () {
          state.index += 1;
          if (last) renderEnd(); else renderQuestion();
        }
      });
      actions.replaceChildren(next);
      next.focus({ preventScroll: true });
    }
  }

  function renderEnd() {
    var total = maxPoints();
    var pct = Math.round((state.score / total) * 100);
    var line = "I scored " + fmt(state.score) + "/" + total + " on the Take the Challenge quiz for " +
      quiz.paper.title + " — " + shareUrl();

    var copied = el("p", { class: "copied", "aria-live": "polite" });
    var shareActions = [el("button", { class: "btn", type: "button", text: "Copy", onclick: function () {
      copyText(line).then(function () { copied.textContent = "Copied to clipboard."; },
        function () { copied.textContent = "Couldn't copy. Select the text above and copy it."; });
    } })];
    if (navigator.share) {
      shareActions.push(el("button", { class: "btn secondary", type: "button", text: "Share…", onclick: function () {
        navigator.share({ text: line }).catch(function () { /* dismissed */ });
      } }));
    }

    var heading = el("h1", { tabindex: "-1", text: "Your score" });
    show([
      el("p", { class: "progress", text: quiz.paper.title }),
      heading,
      el("p", { class: "final", text: fmt(state.score) + " / " + total }),
      el("p", { class: "final-pct", text: pct + "%" }),
      el("div", { class: "share" }, [
        el("p", { class: "share-line", text: line }),
        el("div", { class: "actions" }, shareActions),
        copied
      ]),
      paperLinks(),
      el("div", { class: "actions" }, [el("button", { class: "btn secondary", type: "button", text: "Try again", onclick: start })])
    ], heading);
  }

  function copyText(text) {
    if (navigator.clipboard && window.isSecureContext) return navigator.clipboard.writeText(text);
    return new Promise(function (resolve, reject) {
      var area = el("textarea", { readonly: true, style: "position:fixed;top:0;left:0;opacity:0" });
      area.value = text;
      document.body.appendChild(area);
      area.select();
      var ok = false;
      try { ok = document.execCommand("copy"); } catch (e) { ok = false; }
      document.body.removeChild(area);
      if (ok) resolve(); else reject(new Error("copy failed"));
    });
  }

  load();
})();
