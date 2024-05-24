const path = require('path');

module.exports = {
  entry: './drag-and-drop.js', // 入口文件相对于此webpack.config.js的位置
  output: {
    path: path.resolve(__dirname, 'dist'), // 输出目录相对于此webpack.config.js的位置
    filename: 'bundle.js', // 输出文件
  },
  mode: 'development', // 或者 'production' 根据需要
  module: {
    rules: [
      {
        test: /\.js$/, // 匹配JavaScript文件
        exclude: /node_modules/, // 不处理node_modules目录中的文件
        use: {
          loader: 'babel-loader', // 使用babel-loader来处理JavaScript文件
          options: {
            presets: ['@babel/preset-env'] // 使用@babel/preset-env预设
          }
        }
      }
    ]
  }
};
