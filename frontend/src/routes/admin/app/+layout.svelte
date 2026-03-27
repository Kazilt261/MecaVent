<script lang="ts">
    import { page } from "$app/state";
    import {
        Sidebar,
        SidebarContent,
        SidebarFooter,
        SidebarGroup,
        SidebarGroupContent,
        SidebarGroupLabel,
        SidebarHeader,
        SidebarMenu,
        SidebarMenuButton,
        SidebarMenuItem,
        SidebarInset,
        SidebarProvider,
        SidebarTrigger,
        SidebarRail,
    } from "$lib/components/ui/sidebar";
    import * as DropdownMenu from "$lib/components/ui/dropdown-menu/index.js";

    import { Button } from "$lib/components/ui/button";
    import type { Component } from "svelte";
    import UsersIcon from "@lucide/svelte/icons/users";
    import LinkIcon from "@lucide/svelte/icons/link";
    import CircleUserRoundIcon from "@lucide/svelte/icons/circle-user-round";
    import { toggleMode } from "mode-watcher";
    interface ItemMenu {
        label: string;
        path: string;
        icon: Component<{ class?: string }>;
    }

    const menuItems: ItemMenu[] = [
        {
            label: "Clients",
            path: "/admin/app/clients",
            icon: UsersIcon,
        },
        {
            label: "Client URLs",
            path: "/admin/app/urls",
            icon: LinkIcon,
        },
    ];

    let { data, children } = $props();
    const user = $derived(data.user);
    const pathname = $derived(page.url.pathname);
</script>

<SidebarProvider>
    <Sidebar variant="inset" collapsible="icon">
        <SidebarHeader>
            <div class="flex items-center justify-between px-3 py-2">
                <div>
                    <h1 class="text-base font-semibold">Admin Panel</h1>
                    <p class="text-muted-foreground text-xs">Clients Management</p>
                </div>
                <SidebarTrigger class="md:hidden" />
            </div>
        </SidebarHeader>

        <SidebarContent>
            <SidebarGroup>
                <SidebarGroupLabel>Menu</SidebarGroupLabel>
                <SidebarGroupContent>
                    <SidebarMenu>
                        {#each menuItems as item}
                            <SidebarMenuItem>
                                <SidebarMenuButton class="space-x-2" isActive={pathname.startsWith(item.path)}>
                                    {#snippet child({ props })}
                                        <a href={item.path} class="flex w-full items-center gap-2 px-2 py-1" {...props}>
                                            <item.icon class="inline-block size-4" />
                                            <span>{item.label}</span>
                                        </a>
                                    {/snippet}
                                </SidebarMenuButton>
                            </SidebarMenuItem>
                        {/each}
                    </SidebarMenu>
                </SidebarGroupContent>
            </SidebarGroup>
        </SidebarContent>

        <SidebarFooter>
            <SidebarMenu>
                <SidebarMenuItem>
                    <DropdownMenu.Root>
                        <DropdownMenu.Trigger>
                            {#snippet child({ props })}
                                <Button
                                    variant="ghost"
                                    class="w-full justify-start gap-2 px-2 group-data-[collapsible=icon]:size-8 group-data-[collapsible=icon]:justify-center group-data-[collapsible=icon]:px-0"
                                    {...props}
                                >
                                    <span class="bg-muted inline-flex size-7 shrink-0 items-center justify-center rounded-full border">
                                        <CircleUserRoundIcon class="size-4" />
                                    </span>
                                    <span class="min-w-0 text-left group-data-[collapsible=icon]:hidden">
                                        <span class="block truncate text-sm font-medium">{user.username}</span>
                                        <span class="text-muted-foreground block truncate text-xs">{user.email ?? "No email"}</span>
                                    </span>
                                </Button>
                            {/snippet}
                        </DropdownMenu.Trigger>
                        <DropdownMenu.Content>
                            <DropdownMenu.Item onclick={toggleMode}>Dark/light</DropdownMenu.Item>
                            <DropdownMenu.Item>
                                {#snippet child({ props })}
                                    <a href="/admin/profile" {...props}> Profile </a>
                                {/snippet}
                            </DropdownMenu.Item>

                            <DropdownMenu.Item>
                                {#snippet child({ props })}
                                    <form action="/admin/auth?/logout" method="post">
                                        <button type="submit" class="w-full" {...props}> Logout </button>
                                    </form>
                                {/snippet}
                            </DropdownMenu.Item>
                        </DropdownMenu.Content>
                    </DropdownMenu.Root>
                </SidebarMenuItem>
            </SidebarMenu>
        </SidebarFooter>
    </Sidebar>
    <div class="min-h-[calc(100svh)] w-full p-4">
        <div class="h-full bg-background w-full">
            <header class="bg-background/80 sticky top-0 z-10 flex h-12 items-center gap-2 border-b px-3 backdrop-blur md:px-4">
                <SidebarTrigger />
                <div class="text-sm font-medium">{pathname.startsWith("/admin/app/urls") ? "Client URLs" : "Clients"}</div>
            </header>
            <main class="p-2 md:p-4">
                {@render children?.()}
            </main>
        </div>
    </div>
</SidebarProvider>
