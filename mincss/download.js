var page = require('webpage').create();
page.open(phantom.args[0], function () {
  //page.render('screenshot.png');
  console.log(page.content);
  phantom.exit();
});
