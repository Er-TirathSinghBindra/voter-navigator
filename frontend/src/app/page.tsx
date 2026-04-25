import Link from 'next/link';

export default function Home() {
  return (
    <main className="landing-container" role="main">
      <header>
        <h1>The Civic Navigator</h1>
        <p>
          Your personalized, intelligent election assistant. Navigate polling locations,
          track important deadlines, and decode complex civic jargon effortlessly.
        </p>
      </header>

      <section aria-label="Call to action">
        <Link href="/dashboard" className="primary-button" style={{ textDecoration: 'none', display: 'inline-block' }}>
          Get Started Securely
        </Link>
      </section>
      
      <footer style={{ marginTop: '3rem', color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
        <p>Privacy First: We do not store your location or personal data.</p>
      </footer>
    </main>
  );
}
