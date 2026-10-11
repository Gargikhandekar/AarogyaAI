import { ReactNode } from 'react';
import Navbar from './Navbar';

interface LayoutProps {
  children: ReactNode;
  showNavbar?: boolean;
  transparentNav?: boolean;
  fullWidth?: boolean;
}

export default function Layout({
  children,
  showNavbar = true,
  transparentNav = false,
  fullWidth = false,
}: LayoutProps) {
  return (
    <div className="min-h-screen flex flex-col">
      {showNavbar && <Navbar transparent={transparentNav} />}
      <main className={`flex-1 ${showNavbar ? 'pt-16' : ''} ${fullWidth ? '' : ''}`}>
        {children}
      </main>
    </div>
  );
}
