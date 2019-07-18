var fs = require("fs");
var request = require("request");

function compile(file) {
  const host = "https://latexonline.cc/data";
  const params = "?command=pdflatex&target=main.tex";
  request
    .post({
      url: host + params,
      formData: {
        file: fs.readFileSync(file)
      }
    })

    .on("response", function(response) {
      console.log(response.statusCode); // 200
      console.log(response); // 'image/png'
    });
}

compile("main.tar.gz");
