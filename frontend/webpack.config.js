const path = require('path');
const HtmlWebpackPlugin = require('html-webpack-plugin');

module.exports = {
    entry: './src/index.js',
    output: {
        path: path.resolve(__dirname, 'dist'),
        filename: 'bundle.[contenthash].js',
        publicPath: '/'
    },
    module: {
        rules: [
            {
                test: /\.js$/,
                exclude: /node_modules/,
                use: {
                    loader: 'babel-loader',
                    options: {
                        presets: ['@babel/preset-env'],
                        plugins: [
                            ['@babel/plugin-transform-react-jsx', {
                                pragma: 'h',
                                pragmaFrag: 'Fragment'
                            }]
                        ]
                    }
                }
            },
            {
                test: /\.css$/,
                use: ['style-loader', 'css-loader', 'postcss-loader']
            }
        ]
    },
    plugins: [
        new HtmlWebpackPlugin({
            template: './index.html',
            favicon: './src/assets/favicon.ico'
        })
    ],
    resolve: {
        alias: {
            'react': 'preact/compat',
            'react-dom': 'preact/compat'
        }
    },
    devServer: {
        port: 3000,
        historyApiFallback: true,
        hot: true,
        proxy: [
            {
                context: ['/api'],
                target: 'http://localhost:8000',
                changeOrigin: true
            }
        ]
    }
};