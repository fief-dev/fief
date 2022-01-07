import Document, { Head, Html, Main, NextScript } from 'next/document';

class MyDocument extends Document {
  render() {
    return (
      <Html lang="en">
        <Head />
        <body className="font-inter antialiased bg-gray-100 text-gray-600">
          <Main />
          <NextScript />
        </body>
      </Html>
    );
  };
}

export default MyDocument;
