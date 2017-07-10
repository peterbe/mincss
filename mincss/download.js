var system = require('system');
var page = require('webpage').create();
page.viewportSize = {width: 1280, height: 1024};
page.settings.resourceTimeout = 5000;
page.onResourceTimeout = function(e) {
  console.log(e.errorCode);   // it'll probably be 408
  console.log(e.errorString); // it'll probably be 'Network timeout on resource'
  console.log(e.url);         // the url whose request timed out
  phantom.exit(2);
};
var url = system.args[1]
page.open(url, function (status) {
  if (status !== 'success') {
    console.log('Unable to load', url);
    phantom.exit(1);
  } else {
    setTimeout(function() {
      page.render('screenshot.png');
      console.log(page.content);
      phantom.exit(0);
    }, 1000)
  }
});
