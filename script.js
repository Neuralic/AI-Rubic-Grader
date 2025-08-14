document.addEventListener('DOMContentLoaded', () => {
    console.log('Portfolio website loaded and ready.');
    fetchGitHubProjects();
    setupScrollListener();
});

function setupScrollListener() {
    const sections = document.querySelectorAll('section');
    const navLinks = document.querySelectorAll('nav a');

    window.addEventListener('scroll', () => {
        let current = '';
        sections.forEach(section => {
            const sectionTop = section.offsetTop;
            if (pageYOffset >= sectionTop - 60) {
                current = section.getAttribute('id');
            }
        });

        navLinks.forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('href').slice(1) === current) {
                link.classList.add('active');
            }
        });
    });
}

async function fetchGitHubProjects() {
    const username = 'Neuralic';
    const featuredProjects = ['Dietary-habit-prediction', 'ai-cold-calling', 'Webchat-AI'];
    const projectsContainer = document.getElementById('projects-container');

    try {
        const response = await fetch(`https://api.github.com/users/${username}/repos?sort=updated`);
        if (!response.ok) {
            throw new Error(`GitHub API returned a ${response.status} status.`);
        }
        const repos = await response.json();

        const selectedRepos = repos.filter(repo => featuredProjects.includes(repo.name));

        if (selectedRepos.length === 0) {
            projectsContainer.innerHTML = '<p>Could not find featured projects. Please check the repository names.</p>';
            return;
        }

        projectsContainer.innerHTML = selectedRepos.map(repo => `
            <div class="project-card">
                <h3>${repo.name}</h3>
                <p>${repo.description || 'No description provided.'}</p>
                <a href="${repo.html_url}" target="_blank" class="cta-button">View on GitHub</a>
            </div>
        `).join('');

    } catch (error) {
        console.error('Error fetching GitHub projects:', error);
        projectsContainer.innerHTML = '<p>Could not fetch project information from GitHub. Please try again later.</p>';
    }
}
