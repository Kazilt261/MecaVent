<script lang="ts">
    //import { LogIn, LoaderCircle } from "@lucide/svelte";
    import { Button } from "$lib/components/ui/button/index.js";
    import Input from "$lib/components/input/input.svelte";
    import { enhance } from "$app/forms";
    import * as Card from "$lib/components/ui/card/index.js";

    let { form } = $props();

    let username = $state("");
    let password = $state("");
    let isLoading = $state(false);
</script>

<section class="relative flex min-h-screen items-center justify-center overflow-hidden px-4 w-full max-w-[screen] ">
    <Card.Root>
        <Card.Header class="w-120 max-w-full">
            <Card.Title class="text-2xl">Sign In</Card.Title>
            <Card.Description>Enter your credentials to access your account.</Card.Description>
        </Card.Header>
        <Card.Content>
            <form class="space-y-4" action="?/login" method="POST" use:enhance>
                {#if form?.error}
                    <p class="text-sm text-destructive">{form.message}</p>
                {/if}
                <Input label="Username" type="text" bind:value={username} placeholder="Enter your username" name="username" />
                <Input label="Password" type="password" bind:value={password} placeholder="Enter your password" name="password" />

                <Button type="submit" disabled={isLoading} class="w-full">
                    {#if isLoading}
                        Loading...
                        <!--LoaderCircle class="size-4 animate-spin" /-->
                    {:else}
                        Sign In
                    {/if}
                </Button>
            </form>
            <form action="?/test" method="POST">
                <button type="submit">test</button>
            </form>
        </Card.Content>
    </Card.Root>
</section>
