import Link from 'next/link';

const links = [
  { href: '/', label: 'Overview' },
  { href: '/sessions', label: 'Sessions' },
  { href: '/compare', label: 'Compare' },
  { href: '/efficiency', label: 'Efficiency' },
  { href: '/hypotheses', label: 'Hypotheses' },
];

export function Nav() {
  return (
    <nav className="border-b border-border bg-card/50 backdrop-blur-sm sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-14">
          <Link href="/" className="text-lg font-semibold text-white tracking-tight">
            Flowstate
          </Link>
          <div className="flex gap-6">
            {links.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className="text-sm text-gray-400 hover:text-white transition-colors"
              >
                {link.label}
              </Link>
            ))}
          </div>
        </div>
      </div>
    </nav>
  );
}
