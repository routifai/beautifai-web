
@app.tool("search_web")
async def search_web(
    query: str, 
    scrape_results: bool = DEFAULT_SCRAPE_RESULTS, 
    max_scraped_pages: int = DEFAULT_MAX_SCRAPED_PAGES
) -> List[types.TextContent]:
    """
    Search the web for current information using Google, with optional content scraping.
    
    Use this tool to find recent information, facts, news, or research on any topic.
    Optionally scrape the full content from the top search results for deeper analysis.
    
    Args:
        query: Search terms to find information (e.g., "current weather Tokyo", "Python tutorials")
        scrape_results: Whether to scrape full content from search results (default: True)
        max_scraped_pages: Maximum number of search results to scrape (default: 3, range: 1-10)
    
    Returns:
        List of MCP TextContent objects with search results and optionally scraped content
    """
    logger.debug(f"Executing search_web with query: {query}, scrape_results: {scrape_results}, max_scraped_pages: {max_scraped_pages}")
    
    try:
        # Generate optimized search queries
        query_agent_output = query_agent.run(
            QueryAgentInputSchema(instruction=query, num_queries=DEFAULT_NUM_QUERIES)
        )
        logger.debug(f"Generated queries: {query_agent_output.queries}")
        
        # Validate API credentials
        api_key = os.getenv("GOOGLE_API_KEY")
        cx = os.getenv("GOOGLE_CX")
        if not api_key or not cx:
            error_msg = "Google API credentials not configured"
            logger.error(error_msg)
            return format_bigdata_response(error_msg)
        
        # Execute search
        search_tool = GoogleSearchApiTool(
            config=GoogleSearchApiToolConfig(
                api_key=api_key, cx=cx, max_results=DEFAULT_MAX_RESULTS
            )
        )
        
        search_results = search_tool.run(
            GoogleSearchApiToolInputSchema(queries=query_agent_output.queries)
        )
        
        logger.debug(f"Retrieved {len(search_results.results)} search results")
        
        # Convert search results to the format expected by format_bigdata_response
        formatted_results = []
        for result in search_results.results:
            formatted_results.append({
                "headline": result.title or "No title",
                "url": result.url,
                "content": result.content or "No preview available",
                "scraped": False  # Flag to track scraping status
            })
        
        # If scraping is enabled, scrape the top results in parallel
        if scrape_results and formatted_results:
            # Clamp max_scraped_pages to reasonable bounds
            max_scraped_pages = max(1, min(max_scraped_pages, 10, len(formatted_results)))
            
            logger.debug(f"Starting parallel scraping of top {max_scraped_pages} results")
            
            # Get URLs from top search results
            urls_to_scrape = [result["url"] for result in formatted_results[:max_scraped_pages]]
            
            # Create scraping tasks for parallel execution
            async def scrape_single_url(index: int, url: str) -> tuple[int, bool, str]:
                """Scrape a single URL and return index, success status, and content."""
                try:
                    logger.debug(f"Scraping URL {index+1}/{len(urls_to_scrape)}: {url}")
                    scraper_tool = WebpageScraperTool()
                    
                    scraped_result = await scraper_tool.run(
                        WebpageScraperToolInputSchema(url=url, include_links=True)
                    )
                    
                    if scraped_result.error:
                        logger.warning(f"Failed to scrape {url}: {scraped_result.error}")
                        return index, False, ""
                    else:
                        if scraped_result.content:
                            logger.debug(f"Successfully scraped {url}")
                            return index, True, scraped_result.content
                        else:
                            return index, False, ""
                        
                except Exception as e:
                    logger.error(f"Error scraping {url}: {e}", exc_info=True)
                    return index, False, ""
            
            # Run all scraping tasks in parallel
            scraping_tasks = [
                scrape_single_url(i, url) 
                for i, url in enumerate(urls_to_scrape)
            ]
            
            # Wait for all scraping tasks to complete
            scraping_results = await asyncio.gather(*scraping_tasks, return_exceptions=True)
            
            # Process results and update formatted_results
            successful_scrapes = 0
            for result in scraping_results:
                if isinstance(result, Exception):
                    logger.error(f"Scraping task failed with exception: {result}")
                    continue
                    
                index, success, content = result
                if success and content:
                    formatted_results[index]["content"] = content
                    formatted_results[index]["scraped"] = True
                    successful_scrapes += 1
            
            logger.debug(f"Successfully scraped {successful_scrapes} out of {max_scraped_pages} pages in parallel")
        
        # Return formatted MCP response
        return format_bigdata_response(formatted_results)
        
    except Exception as e:
        error_msg = f"Error in search_web: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return format_bigdata_response(error_msg)

@app.tool("scrape_urls")
async def scrape_urls(urls: List[str], max_pages: int = 5) -> List[types.TextContent]:
    """
    Scrape content from web pages to get full text content in parallel.
    
    Use this tool to extract complete content from specific web pages like articles,
    blog posts, or documentation when you need the full text from known URLs.
    
    Args:
        urls: List of URLs to scrape (e.g., ["https://example.com/article"])
        max_pages: Maximum number of pages to scrape (default: 5, range: 1-10)
    
    Returns:
        List of MCP TextContent objects with scraped content
    """
    logger.debug(f"Executing scrape_urls with {len(urls)} URLs in parallel")
    
    try:
        # Clamp max_pages to reasonable bounds
        max_pages = max(1, min(max_pages, 10, len(urls)))
        urls_to_process = urls[:max_pages]
        
        async def scrape_single_url(index: int, url: str) -> dict:
            """Scrape a single URL and return the result."""
            try:
                logger.debug(f"Scraping URL {index+1}/{len(urls_to_process)}: {url}")
                scraper_tool = WebpageScraperTool()
                
                scraped_result = await scraper_tool.run(
                    WebpageScraperToolInputSchema(url=url, include_links=True)
                )
                
                if scraped_result.error:
                    logger.warning(f"Failed to scrape {url}: {scraped_result.error}")
                    return {
                        "headline": f"Failed to scrape: {url}",
                        "url": url,
                        "content": f"Error: {scraped_result.error}",
                        "scraped": False
                    }
                else:
                    return {
                        "headline": f"Content from {url}",
                        "url": url,
                        "content": scraped_result.content or "No content available",
                        "scraped": True
                    }
            except Exception as e:
                logger.error(f"Error scraping {url}: {e}", exc_info=True)
                return {
                    "headline": f"Failed to scrape: {url}",
                    "url": url,
                    "content": f"Error: {str(e)}",
                    "scraped": False
                }
        
        # Create scraping tasks for parallel execution
        scraping_tasks = [
            scrape_single_url(i, url) 
            for i, url in enumerate(urls_to_process)
        ]
        
        # Run all scraping tasks in parallel
        scraped_content = await asyncio.gather(*scraping_tasks, return_exceptions=True)
        
        # Handle any exceptions from the gather operation
        final_results = []
        for i, result in enumerate(scraped_content):
            if isinstance(result, Exception):
                logger.error(f"Scraping task {i} failed with exception: {result}")
                final_results.append({
                    "headline": f"Failed to scrape: {urls_to_process[i]}",
                    "url": urls_to_process[i],
                    "content": f"Error: {str(result)}",
                    "scraped": False
                })
            else:
                final_results.append(result)
        
        successful = [item for item in final_results if item.get("scraped", False)]
        logger.debug(
            f"Successfully scraped {len(successful)} out of {len(urls_to_process)} pages in parallel"
        )
        
        # Return formatted MCP response
        return format_bigdata_response(final_results)
        
    except Exception as e:
        error_msg = f"Error in scrape_urls: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return format_bigdata_response(error_msg)


