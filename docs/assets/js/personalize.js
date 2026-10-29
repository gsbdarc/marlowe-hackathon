/* Fill the participant's SUNet ID into the commands on the page. Adapted from the Yens Onboarding site.
 *
 * Pages write `<sunet>` where the SUNet ID goes, and `$USER` in paths. Setting the ID once in the sidebar rewrites
 * both, so a command can be copied straight from the page instead of edited in the terminal, where the typos happen.
 * `$USER` already works as typed in the shell, so an unset one is left plain rather than marked as missing.
 *
 *   - Only inside code: prose such as "your <sunet>" is left alone.
 *   - Each occurrence becomes its own <span>, so an unfilled one can be clicked to jump to the field.
 *   - The literal token stays on the span, so clearing the field puts the placeholders back.
 *
 * The value lives in localStorage (this browser only, never sent anywhere).
 */
(function () {
  'use strict';

  var KEY = 'marlowe-hackathon-sunet';
  var TOKENS = ['<sunet>', '$USER'];
  var NEEDS_VALUE = { '<sunet>': true };                // only these are flagged when the ID is unset

  function read() {
    try { return (localStorage.getItem(KEY) || '').trim(); } catch (e) { return ''; }   // private mode
  }
  function write(value) {
    try { if (value) localStorage.setItem(KEY, value); else localStorage.removeItem(KEY); } catch (e) {}
  }

  // Wrap every occurrence in code in its own span, once
  function wrap() {
    var root = document.querySelector('.main-content');
    if (!root) return;
    Array.prototype.forEach.call(root.querySelectorAll('code, pre'), function (host) {
      if (host.tagName === 'CODE' && host.closest('pre')) return;      // walked as part of its <pre>
      var walker = document.createTreeWalker(host, NodeFilter.SHOW_TEXT, null);
      var texts = [];
      while (walker.nextNode()) texts.push(walker.currentNode);
      texts.forEach(function (node) {
        if (node.parentNode.dataset && node.parentNode.dataset.personalizeToken) return;
        var parts = node.nodeValue.split(/(<sunet>|\$USER\b)/);
        if (parts.length === 1) return;
        var frag = document.createDocumentFragment();
        parts.forEach(function (part) {
          if (TOKENS.indexOf(part) > -1) {
            var span = document.createElement('span');
            span.setAttribute('data-personalize-token', part);
            frag.appendChild(span);
          } else if (part) {
            frag.appendChild(document.createTextNode(part));
          }
        });
        node.parentNode.replaceChild(frag, node);
      });
    });
  }

  function inputs() {
    return Array.prototype.slice.call(document.querySelectorAll('input[data-personalize="sunet"]'));
  }

  function render() {
    var id = read();
    Array.prototype.forEach.call(document.querySelectorAll('[data-personalize-token]'), function (el) {
      var token = el.getAttribute('data-personalize-token');
      el.textContent = id || token;
      if (!id && !NEEDS_VALUE[token]) {                  // a plain $USER: correct as it stands
        el.className = 'personalize-token';
        el.removeAttribute('role');
        el.removeAttribute('tabindex');
        el.title = 'Set your SUNet ID in the sidebar to fill this in';
        return;
      }
      el.className = 'personalize-token' + (id ? '' : ' personalize-token-unset');
      if (id) {
        el.removeAttribute('role');
        el.removeAttribute('tabindex');
        el.title = 'Your SUNet ID; change it in the sidebar';
      } else {
        el.setAttribute('role', 'button');
        el.setAttribute('tabindex', '0');
        el.title = 'Click to set your SUNet ID';
      }
    });
    inputs().forEach(function (input) { if (input !== document.activeElement) input.value = id; });
    Array.prototype.forEach.call(document.querySelectorAll('[data-personalize-status]'), function (box) {
      box.textContent = id ? '✓ commands updated' : '';
    });
  }

  // An unfilled placeholder jumps to the field you can see (desktop sidebar or mobile footer)
  function focusField() {
    var all = inputs();
    var target = all.filter(function (i) { return i.offsetParent !== null; })[0] || all[0];
    if (!target) return;
    target.scrollIntoView({ block: 'center' });
    target.focus();
    target.select();
  }
  document.addEventListener('click', function (e) {
    if (e.target.closest && e.target.closest('.personalize-token-unset')) { e.preventDefault(); focusField(); }
  });
  document.addEventListener('keydown', function (e) {
    if ((e.key === 'Enter' || e.key === ' ') && e.target.classList &&
        e.target.classList.contains('personalize-token-unset')) { e.preventDefault(); focusField(); }
  });

  inputs().forEach(function (input) {
    input.addEventListener('input', function () { write(input.value.trim()); render(); });
  });

  wrap();
  render();
})();
