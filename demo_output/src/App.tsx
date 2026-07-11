import React from 'react';
import './styles.css';

interface ProjectCardProps {
  title: string;
  description: string;
  tech: string[];
  url: string;
  image?: string;
}

export function ProjectCard({ title, description, tech, url, image }: ProjectCardProps) {
  return (
    <a href={url} target="_blank" rel="noopener noreferrer" className="card">
      {image && <img src={image} alt={title} className="card-image" />}
      <h3 className="card-title">{title}</h3>
      <p className="card-description">{description}</p>
      <div className="card-tech">
        {tech.map((t) => (
          <span key={t} className="badge">{t}</span>
        ))}
      </div>
    </a>
  );
}

interface HeroProps {
  name: string;
  tagline: string;
}

export function Hero({ name, tagline }: HeroProps) {
  return (
    <section className="hero">
      <h1 className="hero-name">{name}</h1>
      <p className="hero-tagline">{tagline}</p>
      <div className="hero-actions">
        <a href="#projects" className="btn btn-primary">View Projects</a>
        <a href="#contact" className="btn btn-outline">Contact Me</a>
      </div>
    </section>
  );
}

export function App() {
  const projects = [
    {
      title: "Chief AI",
      description: "Multi-agent orchestrator with 55 specialist agents",
      tech: ["Python", "OpenCode", "Multi-Agent"],
      url: "https://github.com/yogendrachukka01/Chief-AI",
    },
    {
      title: "AdaptiveAgent",
      description: "AI agent that adapts to user behavior",
      tech: ["Python", "Machine Learning"],
      url: "https://github.com/yogendrachukka01/AdaptiveAgent",
    },
  ];

  return (
    <div className="container">
      <Hero name="Yogendra Chukka" tagline="Building AI-powered tools" />
      <section id="projects">
        <h2>Projects</h2>
        <div className="grid-2">
          {projects.map((p) => (
            <ProjectCard key={p.title} {...p} />
          ))}
        </div>
      </section>
    </div>
  );
}
