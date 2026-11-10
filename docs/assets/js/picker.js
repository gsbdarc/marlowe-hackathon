/* Build an sbatch command from drop-downs, so a participant picks options instead of typing them.
 *
 * A `.picker` holds <select>s. One with `data-env="BATCH"` sets a variable before `sbatch` (BATCH=64 sbatch ...); one
 * with `data-flag="-C GPU_MODEL:"` adds an option after it (sbatch -C GPU_MODEL:H200 ...). An option equal to the
 * select's `data-default` is left out of the command, as the job uses it anyway.
 *
 * The code block right after the picker holds the default command, so the page works without JavaScript; its script
 * path (the word ending in .slurm) is kept. A `.picker-says` paragraph right after the code block is rewritten from the
 * picker's `data-says` template: each {name} becomes the chosen option's `data-says`, for the select with that name.
 */
(function () {
  'use strict';

  Array.prototype.forEach.call(document.querySelectorAll('.main-content .picker'), function (picker) {
    var block = picker.nextElementSibling;
    if (!block || !block.classList.contains('highlighter-rouge')) return;
    var code = block.querySelector('code');
    var script = (code.textContent.match(/\S+\.slurm/) || [''])[0];
    var says = block.nextElementSibling;
    if (says && !says.classList.contains('picker-says')) says = null;
    var selects = picker.querySelectorAll('select');

    function render() {
      var env = [], flags = [], sentence = picker.getAttribute('data-says') || '';
      Array.prototype.forEach.call(selects, function (s) {
        var opt = s.options[s.selectedIndex];
        sentence = sentence.replace('{' + s.name + '}', opt.getAttribute('data-says') || opt.text);
        if (s.value === s.getAttribute('data-default')) return;
        if (s.hasAttribute('data-env')) env.push(s.getAttribute('data-env') + '=' + s.value);
        if (s.hasAttribute('data-flag')) flags.push(s.getAttribute('data-flag') + s.value);
      });
      code.textContent = env.concat(['sbatch'], flags, [script]).join(' ');
      if (says) says.textContent = sentence;
    }
    Array.prototype.forEach.call(selects, function (s) { s.addEventListener('change', render); });
    render();
  });
})();
