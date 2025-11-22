import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-inter',
});

export const metadata: Metadata = {
  title: 'Chiku - Your AI Study Buddy',
  description:
    'Executive function assistant to help you plan, organize, and stay on top of your tasks.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang='en' className={inter.variable}>
      <body className='font-sans antialiased'>{children}</body>
    </html>
  );
}
