# Submission

Fork URL: <!-- paste the URL of your fork here -->

## Files to commit

- [ ] `site.yml`: the playbook
- [ ] `group_vars/`: the per-distribution variables

## Questions

Answer in your own words. Where a question asks for output, paste it in a code block.

### Q1. Paste `ansible fleet -m setup -a "filter=ansible_distribution*"`. Which facts did you use to tell the servers apart, and where do facts come from (which module collected them and when)?

**Your answer:**

<!-- replace this line with your answer -->

### Q2. Show how you grouped hosts by their operating system while the playbook runs (`group_by`). Why is that better than writing the distribution into the inventory by hand? What goes wrong with the hand-written version after an OS upgrade?

**Your answer:**

<!-- replace this line with your answer -->

### Q3. Paste a task that uses `when:` and one that uses `loop:` with a condition. In one sentence each: when is a `when:` evaluated (before or after the task is templated), and what does `item` hold in a loop?

**Your answer:**

<!-- replace this line with your answer -->

### Q4. Paste the `block`/`rescue` task and its output on Ubuntu and on Debian. Which one took the rescue path, and why is a `rescue` better than `ignore_errors: true`?

**Your answer:**

<!-- replace this line with your answer -->

### Q5. Paste the `PLAY RECAP` of the first run and of the second (`changed=0`). Which of your tasks would have broken that, and what do `changed_when: false` and `check_mode` tell Ansible?

**Your answer:**

<!-- replace this line with your answer -->

### Q6. Run `ansible-playbook site.yml --limit "mf-d*" --tags packages --check --diff`. What did `--limit`, `--tags` and `--check` each do? Why can you not write `--limit os_Debian` (hint: when does that group exist)? When would you rely on this in production?

**Your answer:**

<!-- replace this line with your answer -->

### Q7. Paste the output of `./verify.sh`. It must end with **ALL CHECKS PASSED**.

**Your answer:**

<!-- replace this line with your answer -->

### Q8. **Tear down.** Paste the output of `./verify-teardown.sh`. It must end with **TEARDOWN VERIFIED**.

**Your answer:**

<!-- replace this line with your answer -->
