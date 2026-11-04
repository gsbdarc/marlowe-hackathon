/* Fill a Slurm job ID into the commands on the page, so they can be copied as they are.
 *
 * The first code block about a job gets a "Job ID" field above it. Typing the ID that `sbatch` printed replaces
 * `<jobid>` in every block about that job, further down the page too. A block's job is its `data-job` attribute
 * (set in Markdown with `{: .marlowe data-job="8gpu" data-job-label="8-GPU job ID" }`), or "job" if it has none.
 * `data-job-label`, on the first block about a job, names its field; without it the field says "Job ID".
 * So a page with one job has one field; a page with two jobs has one for each.
 *
 * Values live in localStorage per page (this browser only, never sent anywhere). Only digits are kept.
 */
(function () {
  'use strict';

  var TOKEN = '<jobid>';
  var root = document.querySelector('.main-content');
  if (!root) return;

  function storageKey(job) { return 'marlowe-hackathon-jobid:' + location.pathname + ':' + job; }
  function read(job) {
    try { return localStorage.getItem(storageKey(job)) || ''; } catch (e) { return ''; }   // private mode
  }
  function write(job, value) {
    try {
      if (value) localStorage.setItem(storageKey(job), value); else localStorage.removeItem(storageKey(job));
    } catch (e) {}
  }

  var blocks = Array.prototype.filter.call(root.querySelectorAll('div.highlighter-rouge'), function (b) {
    return b.textContent.indexOf(TOKEN) > -1;
  });
  if (!blocks.length) return;

  var hasField = {};
  blocks.forEach(function (block) {
    var job = block.getAttribute('data-job') || 'job';
    // Each <jobid> becomes its own span, so it can be filled and emptied again
    var walker = document.createTreeWalker(block, NodeFilter.SHOW_TEXT, null);
    var texts = [];
    while (walker.nextNode()) texts.push(walker.currentNode);
    texts.forEach(function (node) {
      if (node.nodeValue.indexOf(TOKEN) === -1) return;
      var frag = document.createDocumentFragment();
      node.nodeValue.split(TOKEN).forEach(function (part, i) {
        if (i > 0) {
          var span = document.createElement('span');
          span.className = 'jobid-token';
          span.setAttribute('data-jobid', job);
          frag.appendChild(span);
        }
        if (part) frag.appendChild(document.createTextNode(part));
      });
      node.parentNode.replaceChild(frag, node);
    });
    // The field, above the first block about this job only
    if (hasField[job]) return;
    hasField[job] = true;
    var field = document.createElement('label');
    field.className = 'jobid-field';
    var name = document.createElement('span');
    name.className = 'jobid-name';
    name.textContent = block.getAttribute('data-job-label') || 'Job ID';
    var input = document.createElement('input');
    input.type = 'text';
    input.inputMode = 'numeric';
    input.autocomplete = 'off';
    input.spellcheck = false;
    input.placeholder = 'the number sbatch printed';
    input.setAttribute('data-jobid', job);
    field.appendChild(name);
    field.appendChild(input);
    block.parentNode.insertBefore(field, block);
    input.addEventListener('input', function () {
      write(job, input.value.replace(/\D/g, ''));
      render();
    });
  });

  function render() {
    Array.prototype.forEach.call(root.querySelectorAll('span.jobid-token'), function (span) {
      var value = read(span.getAttribute('data-jobid'));
      span.textContent = value || TOKEN;
      span.classList.toggle('jobid-unset', !value);
    });
    Array.prototype.forEach.call(root.querySelectorAll('.jobid-field input'), function (input) {
      if (input !== document.activeElement) input.value = read(input.getAttribute('data-jobid'));
    });
  }
  render();
})();
