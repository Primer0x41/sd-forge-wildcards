import modules.scripts as scripts
from sfw_utils.wildcard_manager import wildcard_manager
class SdForgeWildcardsScript(scripts.Script):
    def title(self):
        return "SD Forge Wildcards"

    def show(self, is_img2img):
        return scripts.AlwaysVisible

    def ui(self, is_img2img):
        return []

    def process(self, p, *args):
        if not wildcard_manager.wildcards:
            wildcard_manager.refresh_wildcards()

        def process_batch(prompts, seeds, subseeds=None, seed_offset=0):
            new_prompts = []
            count = len(prompts)
            current_seeds = seeds if seeds and len(seeds) >= count else [p.seed + i for i in range(count)]
            use_subseed = getattr(p, "subseed_strength", 0) > 0 and subseeds and len(subseeds) >= count

            for i, prompt in enumerate(prompts):
                seed = (current_seeds[i] ^ subseeds[i] if use_subseed else current_seeds[i]) + seed_offset
                new_prompts.append(wildcard_manager.replace_wildcards(prompt, seed=seed))
            return new_prompts

        seeds = getattr(p, 'all_seeds', None)
        subseeds = getattr(p, 'all_subseeds', None)

        prompt_fields = (
            ("all_prompts", "prompt", 0),
            ("all_negative_prompts", "negative_prompt", 1),
            ("all_hr_prompts", "hr_prompt", 2),
            ("all_hr_negative_prompts", "hr_negative_prompt", 3),
        )
        for all_attr, single_attr, seed_offset in prompt_fields:
            all_vals = getattr(p, all_attr, None)
            if all_vals:
                processed = process_batch(all_vals, seeds, subseeds, seed_offset=seed_offset)
                setattr(p, all_attr, processed)
                if processed:
                    setattr(p, single_attr, processed[0])
                    if single_attr == "prompt":
                        p.main_prompt = processed[0]
            else:
                single_val = getattr(p, single_attr, None)
                if single_val:
                    setattr(p, single_attr, wildcard_manager.replace_wildcards(single_val, seed=p.seed + seed_offset))
