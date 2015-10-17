#include "vector.h"
#include "alloc.h"

#include <stdlib.h>

#define STACK_GROW_FACTOR 1.5

/* Free() the vector. */
void free_vector(struct vector *vec)
{
    free(vec->objs);
    free(vec);
}

/* Malloc() a vector with the given initial capacity. */
struct vector *make_vector(int capacity)
{
    struct vector *vec = checked_malloc(sizeof(struct vector));
    vec->capacity = capacity;
    vec->size = 0;
    vec->objs = checked_malloc(capacity * sizeof(void *));
    
    return vec;
}

/* Clear the vector (size = 0). */
void vector_clear(struct vector *vec)
{
    vec->size = 0;
}

/* Returns the item at the back of the vec, or NULL if empty. */
void *vector_back(struct vector *vec)
{
    if (vec->size == 0)
        return NULL;
    return vec->objs[vec->size - 1];
}

/* Pops and returns the item at the top of the vector, or NULL if empty. */
void *vector_pop(struct vector *vec)
{
    if (vec->size == 0)
        return NULL;
    vec->size--;
    return vec->objs[vec->size];
}

/* Add the given void * to the vector. */
void vector_push(struct vector *vec, void *obj)
{
    if (vec->size == vec->capacity)
    {
        vec->capacity *= STACK_GROW_FACTOR;
        vec->objs = checked_realloc(vec->objs, vec->capacity * sizeof(void *));
    }
    vec->size++;
    vec->objs[vec->size - 1] = obj;
}

/* Converts the vector into an (NULL-terminated) array of strings. */
char **vector_to_words(struct vector *vec)
{
    int size = vec->size;
    char **words = malloc((size+1) * sizeof(char *));
    
    for (int i = 0; i < size; ++i)
        words[i] = vec->objs[i];
    words[size] = NULL;
    
    return words;
}
