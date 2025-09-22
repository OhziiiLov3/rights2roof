import tools.vector_store_tool as store
def main():
    #the vector store is initialized at startup
    store.create_store()
    print("Hello from rights2roof!")

if __name__ == "__main__":
    main()
