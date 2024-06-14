const path = require('path');

module.exports = {
  entry: './static/js/drag-and-drop.js',
  output: {
    path: path.resolve(__dirname, 'static/js/dist'),
    filename: 'bundle.js',
  },
  module: {
    rules: [
      {
        test: /\.js$/,
        exclude: /node_modules/,
        use: {
          loader: 'babel-loader',
        },
      },
    ],
  },
};
