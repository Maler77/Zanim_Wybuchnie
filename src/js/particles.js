// Lekki system efektów w pikselach świata; nie uczestniczy w kolizjach ani fizyce gry.
export function createParticleSystem({ maxParticles = 260 } = {}) {
    const particles = [];

    function burst(x, y, {
        count = 10,
        colors = ["#fff1b8", "#ffd166", "#f4a261"],
        speed = 70,
        size = 2,
        life = 0.45,
        spread = Math.PI * 2,
        angle = -Math.PI / 2,
        gravity = 90,
        shape = "square",
    } = {}) {
        for (let i = 0; i < count && particles.length < maxParticles; i++) {
            const direction = angle + (Math.random() - 0.5) * spread;
            const velocity = speed * (0.55 + Math.random() * 0.75);
            const lifetime = life * (0.7 + Math.random() * 0.6);
            particles.push({
                x, y,
                vx: Math.cos(direction) * velocity,
                vy: Math.sin(direction) * velocity,
                gravity,
                size: size * (0.65 + Math.random() * 0.7),
                color: colors[Math.floor(Math.random() * colors.length)],
                life: lifetime,
                maxLife: lifetime,
                shape,
            });
        }
    }

    function update(dt) {
        for (let i = particles.length - 1; i >= 0; i--) {
            const particle = particles[i];
            particle.life -= dt;
            if (particle.life <= 0) {
                particles.splice(i, 1);
                continue;
            }
            particle.vy += particle.gravity * dt;
            particle.x += particle.vx * dt;
            particle.y += particle.vy * dt;
            particle.vx *= Math.exp(-1.8 * dt);
        }
    }

    function draw(ctx) {
        ctx.save();
        for (const particle of particles) {
            const fade = Math.min(1, particle.life / (particle.maxLife * 0.35));
            const size = Math.max(1, particle.size * (0.55 + 0.45 * fade));
            ctx.globalAlpha = fade;
            ctx.fillStyle = particle.color;
            if (particle.shape === "circle") {
                ctx.beginPath();
                ctx.arc(particle.x, particle.y, size / 2, 0, Math.PI * 2);
                ctx.fill();
            } else if (particle.shape === "streak") {
                ctx.save();
                ctx.translate(particle.x, particle.y);
                ctx.rotate(Math.atan2(particle.vy, particle.vx));
                const thickness = Math.max(1, size * 0.3);
                ctx.fillRect(-size * 1.4, -thickness / 2, size * 2.8, thickness);
                ctx.restore();
            } else {
                ctx.fillRect(Math.round(particle.x - size / 2), Math.round(particle.y - size / 2), Math.ceil(size), Math.ceil(size));
            }
        }
        ctx.restore();
    }

    function clear() {
        particles.length = 0;
    }

    return { burst, update, draw, clear, get count() { return particles.length; } };
}
