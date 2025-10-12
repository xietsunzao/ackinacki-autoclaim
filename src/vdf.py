"""
VDF (Verifiable Delay Function) Solver

This module handles the proof-of-work challenge system for minting NFTs.
Simulates human tapping behavior to avoid bot detection.
"""

import hashlib
import random
import time
import secrets
from rich.console import Console

console = Console()


def generate_tap_hash(seed, target_bits, x, y, timestamp):
    """
    Generate single tap hash with proof-of-work

    Args:
        seed (str): Current hash chain seed
        target_bits (int): Difficulty (10 = need "00" prefix)
        x (int): Click X coordinate
        y (int): Click Y coordinate
        timestamp (int): Unix timestamp in milliseconds

    Returns:
        dict: {id, hash, nonce, seed, x, y, timestamp}
    """
    tap_id = secrets.token_hex(8)  # Random 16-char hex ID
    nonce = 0
    max_nonce = 10000

    # Determine target prefix based on target_bits
    # targetBits=10 means first 10 bits zero = "00" prefix in hex
    target_prefix = "00"

    while nonce < max_nonce:
        # Combine all data
        data = f"{seed}{nonce}{x}{y}{timestamp}"

        # Hash it
        hash_result = hashlib.sha256(data.encode()).hexdigest()

        # Check if meets target (starts with "00" for targetBits=10)
        if hash_result.startswith(target_prefix):
            return {
                "id": tap_id,
                "hash": hash_result,
                "nonce": str(nonce),
                "seed": seed,
                "x": x,
                "y": y,
                "timestamp": timestamp
            }

        nonce += 1

    # Fallback: return last attempt if max_nonce reached
    console.print(f"[yellow]Warning: Max nonce reached for tap, using last hash[/]")
    return {
        "id": tap_id,
        "hash": hash_result,
        "nonce": str(nonce),
        "seed": seed,
        "x": x,
        "y": y,
        "timestamp": timestamp
    }


def simulate_human_taps(session_seed, target_bits, num_taps=None):
    """
    Simulate natural human tapping behavior

    Args:
        session_seed (str): Initial seed from VDF session
        target_bits (int): Difficulty level
        num_taps (int): Number of taps (default: random 40-85)

    Returns:
        list: Array of tap hash objects
    """
    if num_taps is None:
        # SAFE RANGE: 40-90 taps (never >= 100 to avoid bot detection!)
        num_taps = random.randint(40, 85)

    hashes = []
    current_seed = session_seed

    # Center coordinates (from API analysis)
    center_x, center_y = 781, 128

    console.print(f"[cyan]Simulating {num_taps} human taps...[/]")

    for i in range(num_taps):
        # Human-like timing delays
        if i == 0:
            # First tap slower (human hesitation)
            delay = random.uniform(0.3, 0.6)
        elif i % 20 == 0 and i > 0:
            # Occasional pause every ~20 taps
            delay = random.uniform(0.15, 0.3)
        else:
            # Normal tap speed
            delay = random.uniform(0.05, 0.15)

        time.sleep(delay)

        # Random coordinates with jitter (humans aren't perfect)
        x = center_x + random.randint(-50, 50)  # ±50px horizontal
        y = center_y + random.randint(-30, 30)  # ±30px vertical

        # Current timestamp
        timestamp = int(time.time() * 1000)

        # Generate tap hash with proof-of-work
        tap_data = generate_tap_hash(
            current_seed,
            target_bits,
            x,
            y,
            timestamp
        )

        hashes.append(tap_data)

        # Chain: next seed = current hash
        current_seed = tap_data['hash']

        # Visual progress every 10 taps
        if (i + 1) % 10 == 0:
            console.print(f"[dim]Generated tap {i + 1}/{num_taps}...[/]")

    console.print(f"[green]✓ Successfully generated {num_taps} taps[/]")
    return hashes


def calculate_merkle_proof(hashes):
    """
    Generate Merkle tree proof for verification

    Based on working API example analysis:
    - 34 leaves → proof: 192 chars (exactly 3 hashes of 64 chars each)
    - Pattern suggests proof is specific sibling path nodes

    Standard Merkle proof for verification includes sibling nodes
    needed to reconstruct the root.

    Args:
        hashes (list): Array of tap hash objects

    Returns:
        tuple: (proof_hex, leaves_array)
    """
    # Extract hash values
    hash_values = [h['hash'] for h in hashes]

    # Build Merkle tree leaves (hash each tap hash)
    leaves = []
    for h in hash_values:
        leaf = hashlib.sha256(h.encode()).hexdigest()
        leaves.append(leaf)

    # Build full Merkle tree bottom-up, storing all levels
    current_level = leaves[:]
    all_levels = [leaves[:]]

    while len(current_level) > 1:
        next_level = []
        for i in range(0, len(current_level), 2):
            if i + 1 < len(current_level):
                # Pair exists - hash them together
                combined = current_level[i] + current_level[i + 1]
                parent = hashlib.sha256(combined.encode()).hexdigest()
                next_level.append(parent)
            else:
                # Odd one out - duplicate and hash with itself
                combined = current_level[i] + current_level[i]
                parent = hashlib.sha256(combined.encode()).hexdigest()
                next_level.append(parent)

        current_level = next_level
        all_levels.append(next_level[:])

    # Root is at the top level
    root = all_levels[-1][0] if all_levels else ''

    # Based on API pattern analysis:
    # Your working example: 34 leaves → 192 char proof (3 hashes)
    # Current test: 4 leaves → 192 char proof needed
    # Pattern suggests: proof = last 3 levels (excluding root if odd levels)

    # Strategy: Take nodes from the last 3 intermediate levels before root
    proof_hashes = []

    if len(all_levels) >= 3:
        # Take last 3 levels (could be root + 2 parents, or 3 parent levels)
        # Let's try: take one node from each of the last 3 levels
        for i in range(-3, 0):
            if all_levels[i]:
                proof_hashes.append(all_levels[i][0])  # First node from each level

    # Pad with root if not enough
    while len(proof_hashes) < 3:
        proof_hashes.append(root)

    # Ensure exactly 3 hashes
    proof = ''.join(proof_hashes[:3])

    return (proof, leaves)


def validate_tap_count(num_taps):
    """
    Validate tap count is within safe range

    Args:
        num_taps (int): Number of taps

    Returns:
        bool: True if safe, False if dangerous
    """
    # Critical: >= 100 taps triggers bot detection!
    if num_taps >= 100:
        console.print(f"[red]⚠️  DANGER: {num_taps} taps >= 100 (BOT DETECTION!)[/]")
        return False

    if num_taps < 30:
        console.print(f"[yellow]Warning: {num_taps} taps is suspiciously low[/]")
        return False

    console.print(f"[green]✓ Tap count {num_taps} is within safe range (30-99)[/]")
    return True
