const path = require('path')

module.exports = {
  src: path.resolve(__dirname, '../src'), // source files
  build: path.resolve(__dirname, '../dist'), // production build files
  static: path.resolve(__dirname, '../public'), // static files to copy to build folder
  assets: path.resolve(__dirname, '../src/assets'), // assets source
  components: path.resolve(__dirname, '../src/components'), // components source
  containers: path.resolve(__dirname, '../src/containers'), // containers source
  pages: path.resolve(__dirname, '../src/pages'), // pages source
}
