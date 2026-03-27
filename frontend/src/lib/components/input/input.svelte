<script lang="ts">
    import { Input } from "$lib/components/ui/input";
    import { Label } from "$lib/components/ui/label";

    interface InputProps {
        id?: string;
        label?: string;
        type?: string;
        name?: string;
        value?: string;
        placeholder?: string;
        onInput?: (event: Event) => void;
    }

    let { id, label, type = "text", name , value = $bindable(), placeholder = "", onInput}: InputProps = $props();
</script>

<div class="flex flex-col space-y-1.5">
    {#if label}
        <Label>{label}</Label>
    {/if}
    <Input type={type} {id} {name} bind:value={value} placeholder={placeholder} oninput={onInput} />
</div>
