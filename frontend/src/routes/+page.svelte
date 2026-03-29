<script>
    import { enhance } from "$app/forms";
    import Button from "$lib/components/ui/button/button.svelte";
    
    let { data } = $props();
</script>

<div class="flex min-h-screen flex-col items-center justify-center gap-4 p-4">
    <h1 class="text-2xl font-bold">Welcome to the application</h1>
    {#if data.user}
        <p class="text-center text-muted-foreground">Hello, {data.user.username}! You have signed in successfully.</p>
    {/if}
    {#if data.tenant_data}
        <p class="text-center text-muted-foreground">You are accessing tenant: {data.tenant_data.name_client}</p>
    {/if}
    <p class="text-center text-muted-foreground">This is the home page. Please sign in to continue.</p>
    {#if data.user}
        <form action="/auth?/logout" method="POST" use:enhance>
            <Button variant="outline" type="submit">Sign Out</Button>
        </form>
    {:else}
        <Button variant="outline" href="/auth">Sign In</Button>
    {/if}
</div>
